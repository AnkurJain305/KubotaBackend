from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import notification_service
from schemas.notification import NotificationCreate, NotificationOut
from typing import List

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/", response_model=NotificationOut)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """Create a new notification"""
    return notification_service.create_notification(db, notification)

@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get notification by ID"""
    notification = notification_service.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.get("/user/{user_id}", response_model=List[NotificationOut])
def get_user_notifications(
    user_id: int, 
    unread_only: bool = False, 
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications for a specific user"""
    return notification_service.get_notifications_for_user(db, user_id, unread_only, limit)

@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read"""
    notification_service.mark_notification_as_read(db, notification_id)
    return {"message": "Notification marked as read"}

@router.patch("/user/{user_id}/read-all")
def mark_all_notifications_read(user_id: int, db: Session = Depends(get_db)):
    """Mark all notifications as read for a user"""
    count = notification_service.mark_all_as_read(db, user_id)
    return {"message": f"{count} notifications marked as read"}

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification"""
    notification_service.delete_notification(db, notification_id)
    return {"message": "Notification deleted successfully"}

@router.get("/summary/user/{user_id}")
def get_notification_summary(user_id: int, db: Session = Depends(get_db)):
    """Get notification summary for a user"""
    return notification_service.get_notification_summary(db, user_id)