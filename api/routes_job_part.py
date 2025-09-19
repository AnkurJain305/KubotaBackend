from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import job_part_service
from schemas.job_part import JobPartCreate, JobPartUpdate, JobPartOut

router = APIRouter(prefix="/job-parts", tags=["Job Parts"])

@router.post("/{job_id}", response_model=JobPartOut)
def add_part_to_job(job_id: int, job_part: JobPartCreate, db: Session = Depends(get_db)):
    """Add part to job"""
    db_job_part = job_part_service.add_part_to_job(db, job_id, job_part)
    if not db_job_part:
        raise HTTPException(status_code=400, detail="Failed to add part to job")
    return db_job_part

@router.get("/job/{job_id}", response_model=list[JobPartOut])
def get_job_parts(job_id: int, db: Session = Depends(get_db)):
    """Get all parts for a job"""
    return job_part_service.get_job_parts(db, job_id)

@router.get("/{job_part_id}", response_model=JobPartOut)
def get_job_part(job_part_id: int, db: Session = Depends(get_db)):
    """Get specific job part"""
    db_job_part = job_part_service.get_job_part(db, job_part_id)
    if not db_job_part:
        raise HTTPException(status_code=404, detail="Job part not found")
    return db_job_part

@router.put("/{job_part_id}", response_model=JobPartOut)
def update_job_part(job_part_id: int, part_update: JobPartUpdate, db: Session = Depends(get_db)):
    """Update job part"""
    db_job_part = job_part_service.update_job_part(db, job_part_id, part_update)
    if not db_job_part:
        raise HTTPException(status_code=404, detail="Job part not found")
    return db_job_part

@router.delete("/{job_part_id}")
def remove_part_from_job(job_part_id: int, db: Session = Depends(get_db)):
    """Remove part from job"""
    success = job_part_service.remove_part_from_job(db, job_part_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job part not found")
    return {"message": "Part removed from job successfully"}

@router.get("/part/{part_number}/usage", response_model=list[JobPartOut])
def get_parts_usage_history(part_number: str, db: Session = Depends(get_db)):
    """Get usage history for specific part"""
    return job_part_service.get_parts_usage_by_part(db, part_number)
