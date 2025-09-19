from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.part import PartsInventory, PartsRequest
from schemas.part import PartsInventoryCreate, PartsInventoryUpdate, PartsRequestCreate
from typing import Optional, List

def create_part(db: Session, part: PartsInventoryCreate) -> Optional[PartsInventory]:
    """Create a new part in inventory"""
    try:
        db_part = PartsInventory(**part.model_dump())
        db.add(db_part)
        db.commit()
        db.refresh(db_part)
        return db_part
    except IntegrityError:
        db.rollback()
        return None

def get_part(db: Session, part_number: str) -> Optional[PartsInventory]:
    """Get part by part number"""
    return db.query(PartsInventory).filter(PartsInventory.part_number == part_number).first()

def get_part_by_id(db: Session, inventory_id: int) -> Optional[PartsInventory]:
    """Get part by inventory ID"""
    return db.query(PartsInventory).filter(PartsInventory.inventory_id == inventory_id).first()

def get_parts(db: Session, skip: int = 0, limit: int = 20) -> List[PartsInventory]:
    """Get list of parts"""
    return db.query(PartsInventory).offset(skip).limit(limit).all()

def get_low_stock_parts(db: Session) -> List[PartsInventory]:
    """Get parts with low stock"""
    return db.query(PartsInventory).filter(
        PartsInventory.current_stock <= PartsInventory.minimum_stock
    ).all()

def search_parts(db: Session, search_term: str) -> List[PartsInventory]:
    """Search parts by name or part number"""
    return db.query(PartsInventory).filter(
        (PartsInventory.part_name.ilike(f"%{search_term}%")) |
        (PartsInventory.part_number.ilike(f"%{search_term}%"))
    ).all()

def update_part(db: Session, part_number: str, part_update: PartsInventoryUpdate) -> Optional[PartsInventory]:
    """Update part information"""
    db_part = db.query(PartsInventory).filter(PartsInventory.part_number == part_number).first()
    if not db_part:
        return None

    update_data = part_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_part, field, value)

    try:
        db.commit()
        db.refresh(db_part)
        return db_part
    except IntegrityError:
        db.rollback()
        return None

def update_stock(db: Session, part_number: str, quantity_change: int) -> Optional[PartsInventory]:
    """Update part stock level"""
    db_part = db.query(PartsInventory).filter(PartsInventory.part_number == part_number).first()
    if not db_part:
        return None

    new_stock = max(0, db_part.current_stock + quantity_change)
    db_part.current_stock = new_stock

    try:
        db.commit()
        db.refresh(db_part)
        return db_part
    except IntegrityError:
        db.rollback()
        return None

def reserve_part(db: Session, part_number: str, quantity: int) -> bool:
    """Reserve parts for a job"""
    db_part = db.query(PartsInventory).filter(PartsInventory.part_number == part_number).first()
    if not db_part or db_part.available_stock < quantity:
        return False

    db_part.reserved_stock += quantity

    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False

def release_reserved_part(db: Session, part_number: str, quantity: int) -> bool:
    """Release reserved parts"""
    db_part = db.query(PartsInventory).filter(PartsInventory.part_number == part_number).first()
    if not db_part:
        return False

    db_part.reserved_stock = max(0, db_part.reserved_stock - quantity)

    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False

def create_parts_request(db: Session, parts_request: PartsRequestCreate) -> Optional[PartsRequest]:
    """Create a new parts request"""
    try:
        db_request = PartsRequest(**parts_request.model_dump())
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request
    except IntegrityError:
        db.rollback()
        return None
