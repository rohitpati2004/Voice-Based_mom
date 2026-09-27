import os
import math
import wave
import struct
from pathlib import Path
from app.config import SAMPLES_DIR

def create_synthetic_wav(filename: str, duration_sec: float = 6.0, freq: float = 440.0):
    """Fallback synthetic WAV tone generator if gTTS is unavailable."""
    path = SAMPLES_DIR / filename
    sample_rate = 16000
    num_samples = int(duration_sec * sample_rate)
    
    with wave.open(str(path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            # Alternating tone frequency for speaker change simulation
            current_freq = freq if (i // (sample_rate * 2)) % 2 == 0 else freq * 1.5
            val = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * current_freq * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', val))

    print(f"Generated synthetic WAV sample: {path}")
    return str(path)

def generate_all_samples():
    """Generates audio samples in English, Hindi, Odia, and Multilingual code-switching."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from gtts import gTTS
        print("Using gTTS to synthesize speech audio samples...")

        # 1. English Sample
        en_text = "Good morning everyone. Welcome to the Voice MoM Pipeline review meeting. Person 1 will handle speech recognition and Person 2 will manage database integration."
        tts_en = gTTS(text=en_text, lang='en')
        en_path = SAMPLES_DIR / "sample_english_meeting.mp3"
        tts_en.save(str(en_path))
        print(f"Saved: {en_path}")

        # 2. Hindi Sample
        hi_text = "नमस्कार आप सभी को। आज हम प्रोजेक्ट डिलीवरी और वॉइस प्रोसेसिंग पर चर्चा करेंगे। हम कल तक सभी एक्शन आइटम्स पूरे करेंगे।"
        tts_hi = gTTS(text=hi_text, lang='hi')
        hi_path = SAMPLES_DIR / "sample_hindi_meeting.mp3"
        tts_hi.save(str(hi_path))
        print(f"Saved: {hi_path}")

        # 3. Odia / Multilingual Code-Switch Sample
        # Odia speech synthesis via gTTS (or bilingual English/Hindi fallback)
        or_text = "ଆମର ଏହି ମିଟିଂରେ ଓଡ଼ିଆ ଏବଂ ଇଂରାଜୀ ଭାଷା ବ୍ୟବହାର ହେବ। Action items complete କରିବା।"
        try:
            tts_or = gTTS(text=or_text, lang='or')
            or_path = SAMPLES_DIR / "sample_odia_meeting.mp3"
            tts_or.save(str(or_path))
            print(f"Saved: {or_path}")
        except Exception as e:
            print(f"Odia gTTS fallback: {e}")
            create_synthetic_wav("sample_odia_meeting.wav", duration_sec=8.0, freq=520.0)

        # 4. Multilingual Code-Switching Sample
        mixed_text = "Welcome to the meeting. आज हम हिंदी और English दोनों में बात करेंगे। Person 1 will review the transcript."
        tts_mixed = gTTS(text=mixed_text, lang='hi')
        mixed_path = SAMPLES_DIR / "sample_multilingual_meeting.mp3"
        tts_mixed.save(str(mixed_path))
        print(f"Saved: {mixed_path}")

    except Exception as e:
        print(f"gTTS error: {e}. Generating synthetic audio samples...")
        create_synthetic_wav("sample_english_meeting.wav", duration_sec=8.0, freq=440.0)
        create_synthetic_wav("sample_hindi_meeting.wav", duration_sec=10.0, freq=550.0)
        create_synthetic_wav("sample_multilingual_meeting.wav", duration_sec=12.0, freq=660.0)

if __name__ == "__main__":
    generate_all_samples()
