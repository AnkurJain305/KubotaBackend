from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import datetime

class JobPartBase(BaseModel):
    part_number: str
    quantity_used: int = 1

class JobPartCreate(JobPartBase):
    pass

class JobPartUpdate(BaseModel):
    quantity_used: Optional[int] = None

class JobPartOut(JobPartBase):
    id: int
    job_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JobPartWithDetails(JobPartOut):
    part_info: Optional[dict] = None  # Part inventory details

    class Config:
        from_attributes = True
