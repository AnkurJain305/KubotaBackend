from __future__ import annotations
from sqlalchemy import String, Text, TIMESTAMP, func, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .ticket import Ticket
    from .machine import Machine
    from .job import Job
    from .part import RepairSchedule, SystemNotification, UserFeedback

class User(Base):
    __tablename__ = "users"

    # Primary key
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str | None] = mapped_column(TIMESTAMP, onupdate=func.now())

    # Relationships
    machines: Mapped[list["Machine"]] = relationship("Machine", back_populates="owner", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    assigned_jobs: Mapped[list["Job"]] = relationship("Job", foreign_keys="[Job.technician_id]", back_populates="technician")
    notifications: Mapped[list["SystemNotification"]] = relationship("SystemNotification", back_populates="user", cascade="all, delete-orphan")
    feedback: Mapped[list["UserFeedback"]] = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
    repair_schedules: Mapped[list["RepairSchedule"]] = relationship("RepairSchedule", foreign_keys="[RepairSchedule.technician_id]", back_populates="technician")

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, name='{self.name}', email='{self.email}')>"
