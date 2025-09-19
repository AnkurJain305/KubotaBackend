from typing import List, Optional
from sqlalchemy import String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ticket import Ticket
    from .user import User
    from .job_part import JobPart

class Job(Base):
    __tablename__ = "jobs"

    # Primary key
    job_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Job information
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id"), nullable=True)

    # Status and timing
    status: Mapped[str] = mapped_column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled
    scheduled_date: Mapped[Optional[TIMESTAMP]] = mapped_column(TIMESTAMP, nullable=True)
    completed_date: Mapped[Optional[TIMESTAMP]] = mapped_column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[Optional[TIMESTAMP]] = mapped_column(TIMESTAMP, onupdate=func.now())

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="jobs")
    technician: Mapped[Optional["User"]] = relationship("User", foreign_keys=[technician_id], back_populates="assigned_jobs")
    job_parts: Mapped[List["JobPart"]] = relationship("JobPart", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Job(id={self.job_id}, ticket={self.ticket_id}, status='{self.status}')>"
