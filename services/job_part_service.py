from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.job_part import JobPart
from models.part import PartsInventory
from schemas.job_part import JobPartCreate, JobPartUpdate
from typing import Optional, List

def add_part_to_job(db: Session, job_id: int, job_part: JobPartCreate) -> Optional[JobPart]:
    """Add part to job"""
    try:
        # Check if part exists in inventory
        part_exists = db.query(PartsInventory).filter(
            PartsInventory.part_number == job_part.part_number
        ).first()

        if not part_exists:
            return None

        db_job_part = JobPart(
            job_id=job_id,
            **job_part.model_dump()
        )
        db.add(db_job_part)
        db.commit()
        db.refresh(db_job_part)
        return db_job_part
    except IntegrityError:
        db.rollback()
        return None

def get_job_parts(db: Session, job_id: int) -> List[JobPart]:
    """Get all parts for a job"""
    return db.query(JobPart).filter(JobPart.job_id == job_id).all()

def get_job_part(db: Session, job_part_id: int) -> Optional[JobPart]:
    """Get specific job part"""
    return db.query(JobPart).filter(JobPart.id == job_part_id).first()

def update_job_part(db: Session, job_part_id: int, part_update: JobPartUpdate) -> Optional[JobPart]:
    """Update job part"""
    db_job_part = db.query(JobPart).filter(JobPart.id == job_part_id).first()
    if not db_job_part:
        return None

    update_data = part_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job_part, field, value)

    try:
        db.commit()
        db.refresh(db_job_part)
        return db_job_part
    except IntegrityError:
        db.rollback()
        return None

def remove_part_from_job(db: Session, job_part_id: int) -> bool:
    """Remove part from job"""
    db_job_part = db.query(JobPart).filter(JobPart.id == job_part_id).first()
    if not db_job_part:
        return False

    db.delete(db_job_part)
    db.commit()
    return True

def get_parts_usage_by_part(db: Session, part_number: str) -> List[JobPart]:
    """Get usage history for a specific part"""
    return db.query(JobPart).filter(JobPart.part_number == part_number).all()
