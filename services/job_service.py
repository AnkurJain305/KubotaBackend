from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.job import Job
from schemas.job import JobCreate, JobUpdate
from typing import Optional, List
from datetime import datetime

def create_job(db: Session, job: JobCreate) -> Optional[Job]:
    """Create a new job"""
    try:
        db_job = Job(**job.model_dump())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except IntegrityError:
        db.rollback()
        return None

def get_job(db: Session, job_id: int) -> Optional[Job]:
    """Get job by ID"""
    return db.query(Job).filter(Job.job_id == job_id).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 20) -> List[Job]:
    """Get list of jobs with pagination"""
    return db.query(Job).offset(skip).limit(limit).all()

def get_jobs_by_ticket(db: Session, ticket_id: int) -> List[Job]:
    """Get jobs for a specific ticket"""
    return db.query(Job).filter(Job.ticket_id == ticket_id).all()

def get_jobs_by_technician(db: Session, technician_id: int) -> List[Job]:
    """Get jobs assigned to a specific technician"""
    return db.query(Job).filter(Job.technician_id == technician_id).all()

def get_jobs_by_status(db: Session, status: str) -> List[Job]:
    """Get jobs by status"""
    return db.query(Job).filter(Job.status == status).all()

def update_job(db: Session, job_id: int, job_update: JobUpdate) -> Optional[Job]:
    """Update job information"""
    db_job = db.query(Job).filter(Job.job_id == job_id).first()
    if not db_job:
        return None

    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)

    try:
        db.commit()
        db.refresh(db_job)
        return db_job
    except IntegrityError:
        db.rollback()
        return None

def delete_job(db: Session, job_id: int) -> bool:
    """Delete job"""
    db_job = db.query(Job).filter(Job.job_id == job_id).first()
    if not db_job:
        return False

    db.delete(db_job)
    db.commit()
    return True

def assign_technician(db: Session, job_id: int, technician_id: int) -> Optional[Job]:
    """Assign technician to job"""
    db_job = db.query(Job).filter(Job.job_id == job_id).first()
    if not db_job:
        return None

    db_job.technician_id = technician_id
    if db_job.status == "scheduled":
        db_job.status = "in_progress"

    try:
        db.commit()
        db.refresh(db_job)
        return db_job
    except IntegrityError:
        db.rollback()
        return None

def complete_job(db: Session, job_id: int) -> Optional[Job]:
    """Mark job as completed"""
    from datetime import datetime

    db_job = db.query(Job).filter(Job.job_id == job_id).first()
    if not db_job:
        return None

    db_job.status = "completed"
    db_job.completed_date = datetime.now() #type: ignore

    try:
        db.commit()
        db.refresh(db_job)
        return db_job
    except IntegrityError:
        db.rollback()
        return None
