from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, TIMESTAMP, ForeignKey, func
from .base import Base

if TYPE_CHECKING:
    from .machine import Machine
    from .user import User
    from .job import Job
    from .part import PartsRequest, RepairSchedule, SystemNotification, UserFeedback


class Ticket(Base):
    __tablename__ = "tickets"

    # Primary key
    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Issue information
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    issue_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    priority: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships (FKs)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.machine_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    cause_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, onupdate=func.now())

    # Relationships
    machine: Mapped[Machine] = relationship("Machine", back_populates="tickets")
    user: Mapped[User] = relationship("User", back_populates="tickets")
    jobs: Mapped[List[Job]] = relationship(
        "Job", back_populates="ticket", cascade="all, delete-orphan"
    )
    parts_requests: Mapped[List[PartsRequest]] = relationship(
        "PartsRequest", back_populates="ticket", cascade="all, delete-orphan"
    )
    repair_schedule: Mapped[Optional[RepairSchedule]] = relationship(
        "RepairSchedule", back_populates="ticket", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[List[SystemNotification]] = relationship(
        "SystemNotification", back_populates="ticket", cascade="all, delete-orphan"
    )
    feedback: Mapped[List[UserFeedback]] = relationship(
        "UserFeedback", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.ticket_id}, type='{self.issue_type}', status='{self.status}')>"

