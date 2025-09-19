from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

# Parts Inventory Schemas
class PartsInventoryBase(BaseModel):
    part_number: str
    part_name: str
    description: Optional[str] = None
    minimum_stock: Optional[int] = 0
    cost: Optional[Decimal] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None

class PartsInventoryCreate(PartsInventoryBase):
    current_stock: int = 0

class PartsInventoryUpdate(BaseModel):
    part_name: Optional[str] = None
    description: Optional[str] = None
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    cost: Optional[Decimal] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None

class PartsInventoryOut(PartsInventoryBase):
    inventory_id: int
    current_stock: int
    reserved_stock: int
    available_stock: int
    stock_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Parts Request Schemas
class PartsRequestBase(BaseModel):
    part_number: str
    quantity_requested: int = 1
    priority: Optional[int] = 1
    notes: Optional[str] = None

class PartsRequestCreate(PartsRequestBase):
    ticket_id: int

class PartsRequestUpdate(BaseModel):
    quantity_requested: Optional[int] = None
    quantity_fulfilled: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    estimated_arrival: Optional[datetime] = None
    notes: Optional[str] = None

class PartsRequestOut(PartsRequestBase):
    id: int
    ticket_id: int
    quantity_fulfilled: int
    status: str
    estimated_arrival: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
