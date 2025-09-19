from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .base import Base

class Machine(Base):
    __tablename__ = "machines"

    # Primary key
    machine_id = Column(Integer, primary_key=True, index=True)

    # Machine information
    machine_name = Column(String(255), nullable=False)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="machines")
    tickets = relationship("Ticket", back_populates="machine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Machine(id={self.machine_id}, name='{self.machine_name}', model='{self.model}')>"
