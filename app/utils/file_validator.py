import os
import subprocess
from pathlib import Path
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

class FileValidationError(Exception):
    """Custom exception raised when input file fails validation."""
    pass

def validate_uploaded_file(file_path: str | Path) -> dict:
    path = Path(file_path)
    
    if not path.exists():
        raise FileValidationError(f"File not found: {path.name}")
        
    if path.stat().st_size == 0:
        raise FileValidationError(f"Uploaded file '{path.name}' is empty (0 bytes).")
        
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
        
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise FileValidationError(
            f"File size ({size_mb:.1f} MB) exceeds maximum limit of {MAX_FILE_SIZE_MB} MB."
        )

    # Use ffprobe to verify audio/video stream integrity
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type,duration",
            "-of", "default=noprint_wrappers=1",
            str(path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0 and "Invalid data found" in result.stderr:
            raise FileValidationError(f"File '{path.name}' is corrupted or unreadable audio/video.")
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise e
        # If ffprobe missing or unexpected error, fall back to basic size check
        pass

    return {
        "valid": True,
        "filename": path.name,
        "extension": ext,
        "size_mb": round(size_mb, 2)
    }
