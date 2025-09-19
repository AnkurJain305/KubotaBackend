from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, func
from .base import Base

class Cause(Base):
    __tablename__ = "causes"

    # Primary key
    cause_id = Column(Integer, primary_key=True, index=True)

    # Cause information
    cause_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # mechanical, electrical, hydraulic, etc.

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Cause(id={self.cause_id}, name='{self.cause_name}')>"
