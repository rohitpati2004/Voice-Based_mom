from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class JobUploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    progress: int
    stage: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class TranscriptSegmentSchema(BaseModel):
    speaker: str
    start: float
    end: float
    text: str
    language: str
    confidence: float

class SpeakerStatSchema(BaseModel):
    speaker: str
    speaking_duration_seconds: float
    speaking_duration_formatted: str
    speaking_proportion_percent: float
    segment_count: int
    primary_language: str
    languages: List[str]

class KeyDiscussionPointSchema(BaseModel):
    topic: str
    points: List[str]

class DecisionSchema(BaseModel):
    speaker: str
    timestamp: str
    decision: str

class ActionItemSchema(BaseModel):
    assignee: str
    task: str
    status: str
    timestamp: str

class MoMResultSchema(BaseModel):
    job_id: str
    filename: str
    meeting_title: str
    summary: str
    statistics: Dict[str, Any]
    key_discussion_points: List[KeyDiscussionPointSchema]
    decisions: List[DecisionSchema]
    action_items: List[ActionItemSchema]
    transcript: List[TranscriptSegmentSchema]
