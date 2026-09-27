from typing import List, Dict, Any

class TimestampAligner:
    @staticmethod
    def align(asr_segments: List[Dict[str, Any]], diarization_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges ASR text segments with Speaker Diarization intervals by maximum overlap.
        Returns chronologically sorted list of transcript entries with speaker, start, end, text, language, confidence.
        """
        if not diarization_segments:
            # If no diarization available, default to Person 1
            aligned = []
            for seg in asr_segments:
                aligned.append({
                    "speaker": "Person 1",
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "language": seg.get("language", "English"),
                    "confidence": seg.get("confidence", 0.90)
                })
            return aligned

        aligned_transcript = []
        for seg in asr_segments:
            a_start = seg["start"]
            a_end = seg["end"]

            best_speaker = "Person 1"
            max_overlap = 0.0

            for d_seg in diarization_segments:
                d_start = d_seg["start"]
                d_end = d_seg["end"]

                overlap = max(0.0, min(a_end, d_end) - max(a_start, d_start))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = d_seg["speaker"]

            # If no overlap found (e.g. gap), assign nearest speaker
            if max_overlap == 0.0:
                min_dist = float('inf')
                for d_seg in diarization_segments:
                    dist = min(abs(a_start - d_seg["end"]), abs(a_end - d_seg["start"]))
                    if dist < min_dist:
                        min_dist = dist
                        best_speaker = d_seg["speaker"]

            aligned_transcript.append({
                "speaker": best_speaker,
                "start": a_start,
                "end": a_end,
                "text": seg["text"],
                "language": seg.get("language", "English"),
                "confidence": seg.get("confidence", 0.90)
            })

        # Ensure correct chronological order
        aligned_transcript.sort(key=lambda x: x["start"])
        return aligned_transcript
