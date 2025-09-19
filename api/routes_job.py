from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import job_service
from schemas.job import JobCreate, JobUpdate, JobOut

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobOut)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job"""
    db_job = job_service.create_job(db, job)
    if not db_job:
        raise HTTPException(status_code=400, detail="Job creation failed")
    return db_job

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job by ID"""
    db_job = job_service.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@router.get("/", response_model=list[JobOut])
def get_jobs(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of jobs"""
    return job_service.get_jobs(db, skip=skip, limit=limit)

@router.get("/ticket/{ticket_id}", response_model=list[JobOut])
def get_jobs_by_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get jobs for specific ticket"""
    return job_service.get_jobs_by_ticket(db, ticket_id)

@router.get("/technician/{technician_id}", response_model=list[JobOut])
def get_jobs_by_technician(technician_id: int, db: Session = Depends(get_db)):
    """Get jobs assigned to specific technician"""
    return job_service.get_jobs_by_technician(db, technician_id)

@router.get("/status/{status}", response_model=list[JobOut])
def get_jobs_by_status(status: str, db: Session = Depends(get_db)):
    """Get jobs by status"""
    return job_service.get_jobs_by_status(db, status)

@router.patch("/{job_id}", response_model=JobOut)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    """Update job information"""
    db_job = job_service.update_job(db, job_id, job_update)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete job"""
    success = job_service.delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}

@router.patch("/{job_id}/assign/{technician_id}", response_model=JobOut)
def assign_technician(job_id: int, technician_id: int, db: Session = Depends(get_db)):
    """Assign technician to job"""
    db_job = job_service.assign_technician(db, job_id, technician_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@router.patch("/{job_id}/complete", response_model=JobOut)
def complete_job(job_id: int, db: Session = Depends(get_db)):
    """Mark job as completed"""
    db_job = job_service.complete_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job
