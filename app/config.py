import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
EXPORT_DIR = BASE_DIR / "exports"
SAMPLES_DIR = BASE_DIR / "samples"
DATABASE_URL = f"sqlite:///{BASE_DIR}/mom_pipeline.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma",
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"
}

MAX_FILE_SIZE_MB = 500

# Default speech model configuration
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
SUPPORTED_LANGUAGES = ["en", "hi", "or"]  # English, Hindi, Odia
