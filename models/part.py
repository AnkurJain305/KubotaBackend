from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, Float, DateTime, Boolean, ForeignKey, Text, DECIMAL, func
)
from .base import Base
from datetime import datetime

if TYPE_CHECKING:
    from .ticket import Ticket
    from .user import User
    from .job_part import JobPart


class PartsInventory(Base):
    __tablename__ = "parts_inventory"

    # Primary key
    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Part information
    part_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stock management
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=0)

    # Pricing and supplier
    cost: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    # Relationships
    requests: Mapped[List["PartsRequest"]] = relationship("PartsRequest", back_populates="inventory_item")
    job_parts: Mapped[List[JobPart]] = relationship("JobPart", back_populates="part")

    @property
    def available_stock(self) -> int:
        return max(0, self.current_stock - self.reserved_stock)

    @property
    def stock_status(self) -> str:
        if self.available_stock <= 0:
            return "out_of_stock"
        elif self.available_stock <= self.minimum_stock:
            return "low_stock"
        return "in_stock"

    def __repr__(self) -> str:
        return f"<PartsInventory(part='{self.part_number}', stock={self.current_stock})>"


class PartsRequest(Base):
    __tablename__ = "parts_requests"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Request information
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    part_number: Mapped[str] = mapped_column(ForeignKey("parts_inventory.part_number"), nullable=False)
    quantity_requested: Mapped[int] = mapped_column(Integer, default=1)
    quantity_fulfilled: Mapped[int] = mapped_column(Integer, default=0)

    # Status and priority
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=1)

    # Additional info
    estimated_arrival: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="parts_requests")
    inventory_item: Mapped[PartsInventory] = relationship("PartsInventory", back_populates="requests")

    def __repr__(self) -> str:
        return f"<PartsRequest(ticket={self.ticket_id}, part='{self.part_number}', qty={self.quantity_requested})>"


class RepairSchedule(Base):
    __tablename__ = "repair_schedules"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Schedule information
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.ticket_id"), unique=True, nullable=False)
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id"), nullable=True)

    # Timing
    scheduled_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_start_time: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="repair_schedule")
    technician: Mapped[Optional[User]] = relationship("User", foreign_keys=[technician_id], back_populates="repair_schedules")

    def __repr__(self) -> str:
        return f"<RepairSchedule(ticket={self.ticket_id}, scheduled={self.scheduled_date})>"


class SystemNotification(Base):
    __tablename__ = "system_notifications"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Notification content
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Status and priority
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)

    # Additional data
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    # Relationships
    user: Mapped[User] = relationship("User", back_populates="notifications")
    ticket: Mapped[Optional[Ticket]] = relationship("Ticket", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<SystemNotification(user={self.user_id}, type='{self.notification_type}')>"


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Feedback information
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional data
    specific_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    # Relationships
    user: Mapped[User] = relationship("User", back_populates="feedback")
    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<UserFeedback(user={self.user_id}, ticket={self.ticket_id}, rating={self.rating})>"
