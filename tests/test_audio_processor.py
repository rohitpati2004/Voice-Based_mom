import pytest
from pathlib import Path
from app.utils.file_validator import validate_uploaded_file, FileValidationError
from app.pipeline.audio_processor import AudioProcessor
from scripts.generate_samples import create_synthetic_wav

def test_file_validator_valid_and_invalid(tmp_path):
    # Test valid wav file
    valid_file = tmp_path / "test.wav"
    create_synthetic_wav(str(valid_file.name), duration_sec=2.0)
    
    # Copy generated file to tmp_path
    from app.config import SAMPLES_DIR
    sample_wav = SAMPLES_DIR / valid_file.name
    
    info = validate_uploaded_file(sample_wav)
    assert info["valid"] is True
    assert info["extension"] == ".wav"

    # Test invalid extension
    invalid_file = tmp_path / "test.xyz"
    invalid_file.write_text("dummy data")
    with pytest.raises(FileValidationError):
        validate_uploaded_file(invalid_file)

    # Test empty file
    empty_file = tmp_path / "empty.mp3"
    empty_file.write_bytes(b"")
    with pytest.raises(FileValidationError):
        validate_uploaded_file(empty_file)

def test_audio_processor_conversion(tmp_path):
    sample_src = tmp_path / "input_tone.wav"
    create_synthetic_wav("input_tone.wav", duration_sec=3.0)
    
    from app.config import SAMPLES_DIR
    src_file = SAMPLES_DIR / "input_tone.wav"

    out_norm = tmp_path / "normalized.wav"
    res = AudioProcessor.convert_to_wav(src_file, out_norm)

    assert out_norm.exists()
    assert res["sample_rate"] == 16000
    assert res["channels"] == 1
    assert res["duration_seconds"] > 0
