from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional

class MachineBase(BaseModel):
    machine_name: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None

class MachineCreate(MachineBase):
    user_id: int

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None

class MachineOut(MachineBase):
    machine_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MachineWithOwner(MachineOut):
    owner: Optional[dict] = None  # Will contain user info

    class Config:
        from_attributes = True
