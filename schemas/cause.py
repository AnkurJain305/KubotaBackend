from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CauseBase(BaseModel):
    cause_name: str
    description: Optional[str] = None
    category: Optional[str] = None

class CauseCreate(CauseBase):
    pass

class CauseUpdate(BaseModel):
    cause_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class CauseOut(CauseBase):
    cause_id: int
    created_at: datetime

    class Config:
        from_attributes = True
