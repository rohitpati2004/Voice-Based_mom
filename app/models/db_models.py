import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON
from app.database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size_mb = Column(Float, default=0.0)
    status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    progress = Column(Integer, default=0)            # 0 to 100
    stage = Column(String(100), default="Queued")    # Stage label
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)        # Full structured MoM result
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
