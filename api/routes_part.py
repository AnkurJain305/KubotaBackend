from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import part_service
from schemas.part import PartsInventoryCreate, PartsInventoryUpdate, PartsInventoryOut, PartsRequestCreate, PartsRequestOut

router = APIRouter(prefix="/parts", tags=["Parts Inventory"])

# Parts Inventory Endpoints
@router.post("/", response_model=PartsInventoryOut)
def create_part(part: PartsInventoryCreate, db: Session = Depends(get_db)):
    """Create a new part in inventory"""
    db_part = part_service.create_part(db, part)
    if not db_part:
        raise HTTPException(status_code=400, detail="Part creation failed or part number already exists")
    return db_part

@router.get("/{part_number}", response_model=PartsInventoryOut)
def get_part(part_number: str, db: Session = Depends(get_db)):
    """Get part by part number"""
    db_part = part_service.get_part(db, part_number)
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@router.get("/", response_model=list[PartsInventoryOut])
def get_parts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of parts"""
    return part_service.get_parts(db, skip=skip, limit=limit)

@router.get("/search/{search_term}", response_model=list[PartsInventoryOut])
def search_parts(search_term: str, db: Session = Depends(get_db)):
    """Search parts by name or part number"""
    return part_service.search_parts(db, search_term)

@router.get("/status/low-stock", response_model=list[PartsInventoryOut])
def get_low_stock_parts(db: Session = Depends(get_db)):
    """Get parts with low stock"""
    return part_service.get_low_stock_parts(db)

@router.patch("/{part_number}", response_model=PartsInventoryOut)
def update_part(part_number: str, part_update: PartsInventoryUpdate, db: Session = Depends(get_db)):
    """Update part information"""
    db_part = part_service.update_part(db, part_number, part_update)
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@router.patch("/{part_number}/stock", response_model=PartsInventoryOut)
def update_stock(part_number: str, quantity_change: int, db: Session = Depends(get_db)):
    """Update part stock level"""
    db_part = part_service.update_stock(db, part_number, quantity_change)
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@router.post("/{part_number}/reserve")
def reserve_part(part_number: str, quantity: int, db: Session = Depends(get_db)):
    """Reserve parts for a job"""
    success = part_service.reserve_part(db, part_number, quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot reserve parts - insufficient stock")
    return {"message": "Parts reserved successfully"}

@router.post("/{part_number}/release")
def release_reserved_part(part_number: str, quantity: int, db: Session = Depends(get_db)):
    """Release reserved parts"""
    success = part_service.release_reserved_part(db, part_number, quantity)
    if not success:
        raise HTTPException(status_code=404, detail="Part not found")
    return {"message": "Reserved parts released successfully"}

# Parts Request Endpoints
@router.post("/requests", response_model=PartsRequestOut)
def create_parts_request(parts_request: PartsRequestCreate, db: Session = Depends(get_db)):
    """Create a new parts request"""
    db_request = part_service.create_parts_request(db, parts_request)
    if not db_request:
        raise HTTPException(status_code=400, detail="Parts request creation failed")
    return db_request
