from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.machine import Machine
from schemas.machine import MachineCreate, MachineUpdate
from typing import Optional, List

def create_machine(db: Session, machine: MachineCreate) -> Optional[Machine]:
    """Create a new machine"""
    try:
        db_machine = Machine(**machine.model_dump())
        db.add(db_machine)
        db.commit()
        db.refresh(db_machine)
        return db_machine
    except IntegrityError:
        db.rollback()
        return None

def get_machine(db: Session, machine_id: int) -> Optional[Machine]:
    """Get machine by ID"""
    return db.query(Machine).filter(Machine.machine_id == machine_id).first()

def get_machines(db: Session, skip: int = 0, limit: int = 10) -> List[Machine]:
    """Get list of machines"""
    return db.query(Machine).offset(skip).limit(limit).all()

def get_machines_by_user(db: Session, user_id: int) -> List[Machine]:
    """Get machines owned by a specific user"""
    return db.query(Machine).filter(Machine.user_id == user_id).all()

def update_machine(db: Session, machine_id: int, machine_update: MachineUpdate) -> Optional[Machine]:
    """Update machine information"""
    db_machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not db_machine:
        return None

    update_data = machine_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)

    try:
        db.commit()
        db.refresh(db_machine)
        return db_machine
    except IntegrityError:
        db.rollback()
        return None

def delete_machine(db: Session, machine_id: int) -> bool:
    """Delete machine"""
    db_machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not db_machine:
        return False

    db.delete(db_machine)
    db.commit()
    return True
