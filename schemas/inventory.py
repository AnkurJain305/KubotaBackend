from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# AI Workflow Request/Response Schemas
class TicketProcessingRequest(BaseModel):
    user_symptom: str
    user_id: int
    machine_id: int
    machine_type: Optional[str] = "Unknown"
    priority: int = 1

class TicketProcessingResponse(BaseModel):
    success: bool
    ticket_id: Optional[int] = None
    selected_symptom: Optional[str] = None
    suggested_symptoms: List[Dict] = []
    parts_recommendations: List[Dict] = []
    repair_scheduled: bool = False
    parts_available: bool = False
    estimated_repair_date: Optional[datetime] = None
    notifications_sent: List[str] = []
    processing_time: Optional[float] = None
    agent_messages: List[str] = []

class RepairWorkflowRequest(BaseModel):
    ticket_id: int
    technician_id: Optional[int] = None
    preferred_date: Optional[datetime] = None
    force_schedule: bool = False

class RepairWorkflowResponse(BaseModel):
    success: bool
    scheduled: bool = False
    scheduled_date: Optional[datetime] = None
    technician_assigned: Optional[int] = None
    parts_status: Dict[str, Any] = {}
    blocking_parts: List[str] = []
    estimated_completion: Optional[datetime] = None

# User Feedback Schemas
class UserFeedbackBase(BaseModel):
    feedback_type: str
    rating: Optional[int] = None
    comments: Optional[str] = None

class UserFeedbackCreate(UserFeedbackBase):
    user_id: int
    ticket_id: int
    specific_data: Optional[str] = None

class UserFeedbackOut(UserFeedbackBase):
    id: int
    user_id: int
    ticket_id: int
    specific_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
