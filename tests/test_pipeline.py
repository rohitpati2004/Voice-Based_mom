import pytest
from app.pipeline.diarizer import SpeakerDiarizer
from app.pipeline.aligner import TimestampAligner
from app.pipeline.analytics import ConversationAnalytics
from app.pipeline.mom_generator import LocalMoMGenerator
from scripts.generate_samples import create_synthetic_wav
from app.config import SAMPLES_DIR

def test_speaker_diarizer():
    create_synthetic_wav("test_diar.wav", duration_sec=4.0)
    wav_path = SAMPLES_DIR / "test_diar.wav"
    
    diarizer = SpeakerDiarizer(num_speakers=2)
    segments = diarizer.diarize(str(wav_path))

    assert len(segments) > 0
    assert "speaker" in segments[0]
    assert "start" in segments[0]
    assert "end" in segments[0]
    assert segments[0]["speaker"].startswith("Person")

def test_timestamp_aligner():
    asr_segments = [
        {"start": 0.0, "end": 4.0, "text": "Hello world", "language": "English", "confidence": 0.95},
        {"start": 4.1, "end": 8.0, "text": "हम काम कर रहे हैं", "language": "Hindi", "confidence": 0.92}
    ]
    diar_segments = [
        {"start": 0.0, "end": 4.0, "speaker": "Person 1"},
        {"start": 4.0, "end": 8.0, "speaker": "Person 2"}
    ]

    aligned = TimestampAligner.align(asr_segments, diar_segments)
    assert len(aligned) == 2
    assert aligned[0]["speaker"] == "Person 1"
    assert aligned[1]["speaker"] == "Person 2"
    assert aligned[1]["language"] == "Hindi"

def test_conversation_analytics():
    transcript = [
        {"speaker": "Person 1", "start": 0.0, "end": 10.0, "text": "Turn 1", "language": "English"},
        {"speaker": "Person 2", "start": 10.0, "end": 20.0, "text": "Turn 2", "language": "Hindi"},
        {"speaker": "Person 1", "start": 20.0, "end": 30.0, "text": "Turn 3", "language": "English"}
    ]

    stats = ConversationAnalytics.calculate_statistics(transcript, total_audio_duration=30.0)
    assert stats["total_speakers_count"] == 2
    assert stats["total_segments_count"] == 3
    
    p1 = next(s for s in stats["speaker_statistics"] if s["speaker"] == "Person 1")
    assert p1["speaking_duration_seconds"] == 20.0
    assert p1["speaking_proportion_percent"] == 66.7
    assert p1["segment_count"] == 2

def test_local_mom_generator():
    transcript = [
        {"speaker": "Person 1", "start": 0.0, "end": 5.0, "text": "We will review the voice pipeline requirements and design.", "language": "English"},
        {"speaker": "Person 2", "start": 5.0, "end": 10.0, "text": "We agreed to deploy the API integration by tomorrow.", "language": "English"},
        {"speaker": "Person 1", "start": 10.0, "end": 15.0, "text": "Action item: Person 2 will handle test suites.", "language": "English"}
    ]
    stats = ConversationAnalytics.calculate_statistics(transcript, total_audio_duration=15.0)

    mom_gen = LocalMoMGenerator()
    result = mom_gen.generate_mom(transcript, stats)

    assert "summary" in result
    assert len(result["summary"]) > 0
    assert "key_discussion_points" in result
    assert "decisions" in result
    assert "action_items" in result
    assert len(result["action_items"]) > 0
