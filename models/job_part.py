from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

class JobPart(Base):
    __tablename__ = "job_parts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    job_id = Column(Integer, ForeignKey("jobs.job_id"), nullable=False)
    part_number = Column(String(100), ForeignKey("parts_inventory.part_number"), nullable=False)

    # Quantity used
    quantity_used = Column(Integer, default=1)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="job_parts")
    part = relationship("PartsInventory", back_populates="job_parts")

    def __repr__(self):
        return f"<JobPart(job={self.job_id}, part='{self.part_number}', qty={self.quantity_used})>"
