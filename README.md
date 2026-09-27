# Voice-Based Minutes of Meeting (MoM) Processing Pipeline

A voice-processing pipeline for generating structured Minutes of Meeting (MoM) from audio and video recordings. The system features multilingual speech recognition (supporting **English**, **Hindi**, and **Odia**), speaker diarization with persistent labels (`Person 1`, `Person 2`, ...), speaker conversation statistics, local NLP-driven meeting intelligence (executive summary, key points, decisions, and action items), interactive timestamp-synchronized media playback, and multi-format document exporting (PDF, DOCX, JSON).

> [!IMPORTANT]
> **Zero External LLM API Key Requirement**: 
> All processing (ASR, Speaker Diarization, Analytics, and Summarization) is executed **locally using open-source models and libraries**. No paid external LLM services or API keys (OpenAI, Gemini, Groq, Anthropic, etc.) are required.

---

## Key Features

1. **Audio & Video Preprocessing**: Accepts audio (`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`) and video (`.mp4`, `.mkv`, `.webm`, `.avi`) files and normalizes them using FFmpeg to 16kHz mono WAV.
2. **Speaker Diarization**: Detects speaker turns using frame energy analysis and spectral clustering to assign consistent speaker labels (`Person 1`, `Person 2`, `Person 3`).
3. **Multilingual ASR**: Transcribes speech with timestamps and detects languages across **English**, **Hindi** (`हिन्दी`), and **Odia** (`ଓଡ଼ିଆ`), including code-switching.
4. **Timestamp & Speaker Alignment**: Aligns ASR segment boundaries with speaker intervals.
5. **Speaker Analytics**: Computes total speaking duration (in seconds and `HH:MM:SS`), speaking percentage proportions, segment counts, and language breakdown per participant.
6. **Local MoM Intelligence**:
   - Executive Summary
   - Key Discussion Points
   - Decisions Made
   - Action Items with assignees (`Person X`) and timestamps
7. **Web UI & Synchronized Player**: Modern dark-mode glassmorphism interface with an interactive player—clicking any transcript segment jumps playback directly to that timestamp.
8. **Multi-Format Export**: One-click exports to **PDF**, **DOCX**, and **JSON**.

---

## High-Level Architecture

```
USER
  │
  ▼
Web UI / FastAPI API
  │
  ▼
File Validation & Upload (/api/upload)
  │
  ▼
Audio/Video Preprocessing (FFmpeg 16kHz WAV)
  │
  ├──────────────────────────────┐
  ▼                              ▼
Speaker Diarization            Multilingual Speech-to-Text
(Spectral Clustering)          (Whisper English/Hindi/Odia)
  │                              │
  └──────────────┬───────────────┘
                 ▼
Timestamp & Speaker Alignment Engine
                 │
                 ▼
Speaker Conversation Analytics
                 │
                 ▼
Local Open-Source MoM Intelligence
(Summary, Key Points, Decisions, Action Items)
                 │
                 ▼
SQLite Database & Storage
                 │
                 ▼
Web Dashboard Sync Player & Export Utility (PDF / DOCX / JSON)
```

---

## Tech Stack & Model Selection

| Component | Technology | Rationale / Explanation |
| :--- | :--- | :--- |
| **Backend API** | Python 3.12 + FastAPI + SQLite | Async background task handling, lightweight database, REST API delivery. |
| **Audio Processing** | FFmpeg + Librosa + Scipy | Handles video-to-audio extraction, resampling to 16kHz mono WAV, and frame energy estimation. |
| **ASR (Speech-to-Text)** | OpenAI Whisper (`base`/`small`) | Local multilingual ASR natively supporting English, Hindi (`hi`), and Odia (`or`) with timestamps. |
| **Speaker Diarization** | Spectral Clustering + Frame VAD | Offline speaker turn segmentation mapping acoustic features to consistent `Person 1`, `Person 2` labels without HF token requirements. |
| **MoM Summarization & NLP** | Local Transformers + Pattern Parsing | Extractive and abstractive NLP generating structured summaries, key points, decisions, and action items locally. |
| **Document Exporter** | ReportLab + python-docx | Produces formal PDF and DOCX Minutes of Meeting reports. |
| **Frontend UI** | HTML5 + CSS3 (Glassmorphism) + Vanilla JS | Responsive dark-mode interface with interactive audio player synchronization. |

---

## Quick Start Guide

### Prerequisites
- Python 3.10+
- FFmpeg installed and available on system `PATH`.

### 1. Installation

Clone the repository and install the dependencies:

```bash
cd "Project"
pip install -r requirements.txt
```

### 2. Generate Sample Audio Files

Synthesize sample meeting recordings (English, Hindi, Odia, Multilingual):

```bash
python -m scripts.generate_samples
```

The sample recordings will be placed in `samples/`:
- `samples/sample_english_meeting.mp3`
- `samples/sample_hindi_meeting.mp3`
- `samples/sample_odia_meeting.wav`
- `samples/sample_multilingual_meeting.mp3`

### 3. Run Application Server

Launch the FastAPI web server:

```bash
python -m scripts.run
```

Access the application:
- **Web Interface**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Docker Support

Run containerized application with Docker Compose:

```bash
docker-compose up --build
```

---

## Running Automated Tests

Run the full pytest suite:

```bash
python -m pytest tests/
```

---

## REST API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload audio/video file and trigger background pipeline. |
| `GET` | `/api/jobs` | Get list of all meeting jobs. |
| `GET` | `/api/jobs/{job_id}` | Get status, stage, and progress of a specific job. |
| `GET` | `/api/jobs/{job_id}/result` | Get complete structured MoM JSON result. |
| `GET` | `/api/jobs/{job_id}/media` | Stream normalized audio file for player playback. |
| `GET` | `/api/jobs/{job_id}/export/{format}` | Download MoM document in `pdf`, `docx`, or `json` format. |
| `DELETE` | `/api/jobs/{job_id}` | Delete job record and associated files. |

---

## Known Limitations

1. **Speaker Overlap**: Extreme overlapping speech (multiple speakers shouting simultaneously) may reduce diarization boundary precision.
2. **Code-Switching Speed**: Rapid intra-sentential language switching (switching languages mid-phrase) relies on Whisper's frame-level language token probabilities.
3. **Hardware Acceleration**: CPU execution of Whisper `base` model takes ~1.5x real-time; GPU acceleration (CUDA) is recommended for long recordings (>30 mins).
