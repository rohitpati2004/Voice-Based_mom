import uuid
import logging
import shutil
import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, PROCESSED_DIR, EXPORT_DIR, BASE_DIR
from app.database import Base, engine, get_db
from app.models.db_models import JobModel
from app.models.schemas import JobUploadResponse, JobStatusResponse, MoMResultSchema
from app.utils.file_validator import validate_uploaded_file, FileValidationError
from app.utils.exporter import DocumentExporter

from app.pipeline.audio_processor import AudioProcessor
from app.pipeline.asr_engine import ASREngine
from app.pipeline.diarizer import SpeakerDiarizer
from app.pipeline.aligner import TimestampAligner
from app.pipeline.analytics import ConversationAnalytics
from app.pipeline.mom_generator import LocalMoMGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MoM_Pipeline")

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Voice-Based Minutes of Meeting Pipeline API",
    description="Multilingual (English, Hindi, Odia) MoM Pipeline using local open-source models.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instances
asr_engine = ASREngine(model_size="base")
mom_generator = LocalMoMGenerator()

def update_job_status(db: Session, job_id: str, status: str, progress: int, stage: str, error: str = None, result_data: dict = None):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if job:
        job.status = status
        job.progress = progress
        job.stage = stage
        job.error_message = error
        if result_data:
            job.result_data = result_data
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

def run_mom_pipeline_job(job_id: str, file_path: str, original_filename: str):
    """
    Background Task Orchestrating the 6-stage Voice MoM Processing Pipeline.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        logger.info(f"Starting MoM Pipeline Job '{job_id}' for file '{original_filename}'")
        
        # Stage 1: Audio Preprocessing & FFmpeg Normalization (Progress 15%)
        update_job_status(db, job_id, "PROCESSING", 15, "Converting & Normalizing Audio (FFmpeg 16kHz WAV)")
        norm_wav_path = PROCESSED_DIR / f"{job_id}_norm.wav"
        audio_info = AudioProcessor.convert_to_wav(file_path, norm_wav_path)
        total_duration = audio_info["duration_seconds"]

        # Stage 2: Speaker Diarization (Progress 40%)
        update_job_status(db, job_id, "PROCESSING", 40, "Performing Speaker Diarization (Speaker Segmentation)")
        diarizer = SpeakerDiarizer(num_speakers=2)
        diarization_segments = diarizer.diarize(str(norm_wav_path))

        # Stage 3: Multilingual ASR (Progress 65%)
        update_job_status(db, job_id, "PROCESSING", 65, "Multilingual Speech-to-Text Transcription (Whisper)")
        asr_segments = asr_engine.transcribe(norm_wav_path)

        # Stage 4: Timestamp & Speaker Alignment (Progress 80%)
        update_job_status(db, job_id, "PROCESSING", 80, "Aligning Speaker Labels with Transcript Timestamps")
        aligned_transcript = TimestampAligner.align(asr_segments, diarization_segments)

        # Stage 5: Conversation Analytics (Progress 90%)
        update_job_status(db, job_id, "PROCESSING", 90, "Calculating Speaker Statistics & Conversation Analytics")
        stats = ConversationAnalytics.calculate_statistics(aligned_transcript, total_duration)

        # Stage 6: Local MoM Intelligence (Progress 100%)
        update_job_status(db, job_id, "PROCESSING", 95, "Generating MoM Summary, Decisions & Action Items")
        mom_intelligence = mom_generator.generate_mom(aligned_transcript, stats)

        # Build final structured output
        final_result = {
            "job_id": job_id,
            "filename": original_filename,
            "meeting_title": f"Meeting Record - {Path(original_filename).stem.replace('_', ' ').capitalize()}",
            "summary": mom_intelligence["summary"],
            "statistics": stats,
            "key_discussion_points": mom_intelligence["key_discussion_points"],
            "decisions": mom_intelligence["decisions"],
            "action_items": mom_intelligence["action_items"],
            "transcript": aligned_transcript
        }

        update_job_status(db, job_id, "COMPLETED", 100, "Processing Complete", result_data=final_result)
        logger.info(f"Successfully finished job '{job_id}'")

    except Exception as e:
        logger.error(f"Error processing job '{job_id}': {str(e)}", exc_info=True)
        update_job_status(db, job_id, "FAILED", 0, "Processing Failed", error=str(e))
    finally:
        db.close()


@app.post("/api/upload", response_model=JobUploadResponse)
async def upload_meeting_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    safe_filename = f"{job_id}_{file.filename}"
    upload_file_path = UPLOAD_DIR / safe_filename

    # Save uploaded stream
    try:
        with upload_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Validate file format and size
    try:
        file_info = validate_uploaded_file(upload_file_path)
    except FileValidationError as ve:
        if upload_file_path.exists():
            upload_file_path.unlink()
        raise HTTPException(status_code=400, detail=str(ve))

    # Create job entry in SQLite
    new_job = JobModel(
        id=job_id,
        filename=safe_filename,
        original_name=file.filename,
        file_size_mb=file_info["size_mb"],
        status="PENDING",
        progress=5,
        stage="Uploaded & Validated"
    )
    db.add(new_job)
    db.commit()

    # Trigger background pipeline processing
    background_tasks.add_task(run_mom_pipeline_job, job_id, str(upload_file_path), file.filename)

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "PENDING",
        "message": "File uploaded successfully. Voice pipeline processing initiated."
    }

@app.get("/api/jobs", response_model=List[JobStatusResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).all()
    return [
        {
            "job_id": j.id,
            "filename": j.original_name,
            "status": j.status,
            "progress": j.progress,
            "stage": j.stage,
            "error_message": j.error_message,
            "created_at": j.created_at.isoformat(),
            "updated_at": j.updated_at.isoformat()
        } for j in jobs
    ]

@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return {
        "job_id": job.id,
        "filename": job.original_name,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }

@app.get("/api/jobs/{job_id}/result")
def get_job_result(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Job status is '{job.status}'. Results are only available when status is COMPLETED.")
    return job.result_data

@app.get("/api/jobs/{job_id}/media")
def get_job_media(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    norm_wav = PROCESSED_DIR / f"{job_id}_norm.wav"
    if norm_wav.exists():
        return FileResponse(norm_wav, media_type="audio/wav", filename=f"{Path(job.original_name).stem}.wav")
    orig_file = UPLOAD_DIR / job.filename
    if orig_file.exists():
        return FileResponse(orig_file, filename=job.original_name)
    raise HTTPException(status_code=404, detail="Media file not found")

@app.get("/api/jobs/{job_id}/export/{format_type}")
def export_job_report(job_id: str, format_type: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job or job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not found or not completed yet.")

    mom_data = job.result_data
    fmt = format_type.lower()
    base_name = Path(job.original_name).stem

    if fmt == "pdf":
        out_pdf = EXPORT_DIR / f"{job_id}_mom.pdf"
        DocumentExporter.export_pdf(mom_data, out_pdf)
        return FileResponse(out_pdf, media_type="application/pdf", filename=f"{base_name}_MoM.pdf")
    elif fmt == "docx":
        out_docx = EXPORT_DIR / f"{job_id}_mom.docx"
        DocumentExporter.export_docx(mom_data, out_docx)
        return FileResponse(out_docx, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{base_name}_MoM.docx")
    elif fmt == "json":
        out_json = EXPORT_DIR / f"{job_id}_mom.json"
        import json
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(mom_data, f, indent=2, ensure_ascii=False)
        return FileResponse(out_json, media_type="application/json", filename=f"{base_name}_MoM.json")
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Supported formats: pdf, docx, json")

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up stored files
    up_file = UPLOAD_DIR / job.filename
    if up_file.exists():
        up_file.unlink()
    proc_file = PROCESSED_DIR / f"{job_id}_norm.wav"
    if proc_file.exists():
        proc_file.unlink()

    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully."}

# Mount Web Dashboard UI
static_dir = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def read_root():
    return FileResponse(static_dir / "index.html")
