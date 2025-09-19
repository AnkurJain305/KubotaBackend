from pydantic import BaseModel , ConfigDict
from datetime import datetime
from typing import Optional

class TicketBase(BaseModel):
    issue_type: Optional[str] = None
    issue_text: str
    priority: Optional[int] = 1

class TicketCreate(TicketBase):
    machine_id: int
    user_id: int

class TicketUpdate(BaseModel):
    issue_type: Optional[str] = None
    issue_text: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    cause_description: Optional[str] = None

class TicketOut(TicketBase):
    ticket_id: int
    machine_id: int
    user_id: int
    status: str
    cause_description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TicketWithRelations(TicketOut):
    machine: Optional[dict] = None
    user: Optional[dict] = None
    parts_requests: Optional[list] = []

    class Config:
        from_attributes = True
