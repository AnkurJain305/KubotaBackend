from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import cause_service
from schemas.cause import CauseCreate, CauseUpdate, CauseOut

router = APIRouter(prefix="/causes", tags=["Causes"])

@router.post("/", response_model=CauseOut)
def create_cause(cause: CauseCreate, db: Session = Depends(get_db)):
    """Create a new cause"""
    db_cause = cause_service.create_cause(db, cause)
    if not db_cause:
        raise HTTPException(status_code=400, detail="Cause creation failed")
    return db_cause

@router.get("/{cause_id}", response_model=CauseOut)
def get_cause(cause_id: int, db: Session = Depends(get_db)):
    """Get cause by ID"""
    db_cause = cause_service.get_cause(db, cause_id)
    if not db_cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    return db_cause

@router.get("/", response_model=list[CauseOut])
def get_causes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of causes"""
    return cause_service.get_causes(db, skip=skip, limit=limit)

@router.get("/category/{category}", response_model=list[CauseOut])
def get_causes_by_category(category: str, db: Session = Depends(get_db)):
    """Get causes by category"""
    return cause_service.get_causes_by_category(db, category)

@router.get("/search/{search_term}", response_model=list[CauseOut])
def search_causes(search_term: str, db: Session = Depends(get_db)):
    """Search causes by name or description"""
    return cause_service.search_causes(db, search_term)

@router.patch("/{cause_id}", response_model=CauseOut)
def update_cause(cause_id: int, cause_update: CauseUpdate, db: Session = Depends(get_db)):
    """Update cause information"""
    db_cause = cause_service.update_cause(db, cause_id, cause_update)
    if not db_cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    return db_cause

@router.delete("/{cause_id}")
def delete_cause(cause_id: int, db: Session = Depends(get_db)):
    """Delete cause"""
    success = cause_service.delete_cause(db, cause_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cause not found")
    return {"message": "Cause deleted successfully"}
