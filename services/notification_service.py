from sqlalchemy.orm import Session
from models.notification import Notification
from schemas.notification import NotificationCreate
from fastapi import HTTPException
from datetime import datetime
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def create_notification(db: Session, notif_data: NotificationCreate) -> Notification:
    """Create a new notification"""
    try:
        new_notif = Notification(
            user_id=notif_data.user_id,
            message=notif_data.message,
            notification_type=notif_data.notification_type
        )

        db.add(new_notif)
        db.commit()
        db.refresh(new_notif)

        logger.info(f"Created notification for user {notif_data.user_id}")
        return new_notif

    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Notification creation failed: {str(e)}")

def get_notifications_for_user(db: Session, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
    """Get notifications for a user"""
    try:
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    except Exception as e:
        logger.error(f"Failed to get notifications for user {user_id}: {e}")
        return []

def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
    """Get a single notification by ID"""
    return db.query(Notification).filter(Notification.notification_id == notification_id).first()

def mark_notification_as_read(db: Session, notification_id: int) -> None:
    """Mark a notification as read"""
    notification = get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Use update() method instead of direct assignment
    db.query(Notification).filter(Notification.notification_id == notification_id).update(
        {"is_read": True},
        synchronize_session=False
    )
    db.commit()

def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read for a user"""
    try:
        # Use update() with filter
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update(
            {"is_read": True},
            synchronize_session=False
        )
        
        db.commit()
        return result  # Returns the number of rows updated
        
    except Exception as e:
        logger.error(f"Failed to mark notifications as read: {e}")
        db.rollback()
        return 0

def delete_notification(db: Session, notification_id: int) -> bool:
    """Delete a notification"""
    notification = get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return True

def get_notification_summary(db: Session, user_id: int) -> dict:
    """Get notification summary for a user"""
    try:
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

        return {
            "user_id": user_id,
            "total_notifications": total,
            "unread_notifications": unread,
            "read_notifications": total - unread
        }

    except Exception as e:
        logger.error(f"Failed to get notification summary: {e}")
        return {
            "user_id": user_id,
            "total_notifications": 0,
            "unread_notifications": 0,
            "read_notifications": 0
        }