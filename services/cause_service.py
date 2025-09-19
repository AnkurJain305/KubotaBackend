from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.cause import Cause
from schemas.cause import CauseCreate, CauseUpdate
from typing import Optional, List

def create_cause(db: Session, cause: CauseCreate) -> Optional[Cause]:
    """Create a new cause"""
    try:
        db_cause = Cause(**cause.model_dump())
        db.add(db_cause)
        db.commit()
        db.refresh(db_cause)
        return db_cause
    except IntegrityError:
        db.rollback()
        return None

def get_cause(db: Session, cause_id: int) -> Optional[Cause]:
    """Get cause by ID"""
    return db.query(Cause).filter(Cause.cause_id == cause_id).first()

def get_causes(db: Session, skip: int = 0, limit: int = 20) -> List[Cause]:
    """Get list of causes"""
    return db.query(Cause).offset(skip).limit(limit).all()

def get_causes_by_category(db: Session, category: str) -> List[Cause]:
    """Get causes by category"""
    return db.query(Cause).filter(Cause.category == category).all()

def search_causes(db: Session, search_term: str) -> List[Cause]:
    """Search causes by name or description"""
    return db.query(Cause).filter(
        (Cause.cause_name.ilike(f"%{search_term}%")) |
        (Cause.description.ilike(f"%{search_term}%"))
    ).all()

def update_cause(db: Session, cause_id: int, cause_update: CauseUpdate) -> Optional[Cause]:
    """Update cause information"""
    db_cause = db.query(Cause).filter(Cause.cause_id == cause_id).first()
    if not db_cause:
        return None

    update_data = cause_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cause, field, value)

    try:
        db.commit()
        db.refresh(db_cause)
        return db_cause
    except IntegrityError:
        db.rollback()
        return None

def delete_cause(db: Session, cause_id: int) -> bool:
    """Delete cause"""
    db_cause = db.query(Cause).filter(Cause.cause_id == cause_id).first()
    if not db_cause:
        return False

    db.delete(db_cause)
    db.commit()
    return True
