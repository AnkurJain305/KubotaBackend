from pydantic import BaseModel,ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class JobBase(BaseModel):
    ticket_id: int
    technician_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    status: JobStatus = JobStatus.scheduled

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    technician_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[str] = None

class JobOut(JobBase):
    job_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class JobWithParts(JobOut):
    job_parts: Optional[list] = []

    class Config:
        from_attributes = True
