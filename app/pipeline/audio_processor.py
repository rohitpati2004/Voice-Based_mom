import os
import subprocess
from pathlib import Path
import wave
import contextlib

class AudioProcessingError(Exception):
    """Exception raised when audio extraction or conversion fails."""
    pass

class AudioProcessor:
    @staticmethod
    def convert_to_wav(input_path: str | Path, output_path: str | Path) -> dict:
        """
        Converts any input audio/video file to normalized 16kHz mono WAV audio format.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", str(input_path),
            "-vn",  # Disable video stream if present
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # 16 kHz sample rate
            "-ac", "1",      # Mono channel
            str(output_path)
        ]
        
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if res.returncode != 0:
                raise AudioProcessingError(f"FFmpeg conversion failed: {res.stderr}")
        except subprocess.TimeoutExpired:
            raise AudioProcessingError("FFmpeg audio conversion timed out.")
        except Exception as e:
            if isinstance(e, AudioProcessingError):
                raise e
            raise AudioProcessingError(f"Audio processing error: {str(e)}")
            
        duration = AudioProcessor.get_audio_duration(output_path)
        return {
            "wav_path": str(output_path),
            "sample_rate": 16000,
            "channels": 1,
            "duration_seconds": round(duration, 2)
        }

    @staticmethod
    def get_audio_duration(wav_path: str | Path) -> float:
        """Returns exact audio duration in seconds from WAV header."""
        try:
            with contextlib.closing(wave.open(str(wav_path), 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                if rate == 0:
                    return 0.0
                return frames / float(rate)
        except Exception:
            # Fallback duration via ffprobe
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(wav_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                return float(res.stdout.strip())
            except ValueError:
                return 0.0
