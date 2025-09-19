from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import machine_service
from schemas.machine import MachineCreate, MachineUpdate, MachineOut

router = APIRouter(prefix="/machines", tags=["Machines"])

@router.post("/", response_model=MachineOut)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    """Create a new machine"""
    db_machine = machine_service.create_machine(db, machine)
    if not db_machine:
        raise HTTPException(status_code=400, detail="Machine creation failed")
    return db_machine

@router.get("/{machine_id}", response_model=MachineOut)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    """Get machine by ID"""
    db_machine = machine_service.get_machine(db, machine_id)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.get("/", response_model=list[MachineOut])
def get_machines(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get list of machines"""
    return machine_service.get_machines(db, skip=skip, limit=limit)

@router.get("/user/{user_id}", response_model=list[MachineOut])
def get_machines_by_user(user_id: int, db: Session = Depends(get_db)):
    """Get machines owned by specific user"""
    return machine_service.get_machines_by_user(db, user_id)

@router.patch("/{machine_id}", response_model=MachineOut)
def update_machine(machine_id: int, machine_update: MachineUpdate, db: Session = Depends(get_db)):
    """Update machine information"""
    db_machine = machine_service.update_machine(db, machine_id, machine_update)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.delete("/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    """Delete machine"""
    success = machine_service.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Machine deleted successfully"}
