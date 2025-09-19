from sqlalchemy.orm import Session
from models.ticket import Ticket
from schemas.ticket import TicketCreate, TicketOut
from services.notification_service import create_notification
from schemas.notification import NotificationCreate
from datetime import datetime
import logging

# Import AI service for intelligent processing
from services.ai_service import kubota_ai_service
from schemas.ai_schema import AIRecommendationRequest

logger = logging.getLogger(__name__)

async def create_ticket_with_ai(db: Session, ticket: TicketCreate):
    """
    Enhanced ticket creation with AI-powered parts recommendation
    This replaces your existing create_ticket function
    """
    try:
        # Create the ticket normally
        new_ticket = Ticket(
            issue_type=ticket.issue_type,
            issue_text=ticket.issue_text,
            status="open",
            machine_id=ticket.machine_id,
            user_id=ticket.user_id,
            created_at=datetime.now()
        )

        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        logger.info(f"Created ticket {new_ticket.ticket_id}: {ticket.issue_text[:50]}...")

        # NEW: Get AI recommendations for this ticket
        try:
            ai_request = AIRecommendationRequest(
                user_issue=str(ticket.issue_text),
                issue_type=getattr(ticket, 'issue_type', None),
                machine_series=getattr(ticket, 'machine_series', None),
                max_recommendations=5
            )

            ai_result = await kubota_ai_service.get_ai_recommendations(ai_request)

            if ai_result.success and ai_result.recommended_parts:
                # Create notification with AI recommendations
                parts_summary = ", ".join([
                    p.part_number for p in ai_result.recommended_parts[:3]
                ])

                ai_notification = NotificationCreate(
                    user_id=ticket.user_id,
                    message=f"AI found {len(ai_result.recommended_parts)} recommended parts for your issue: {parts_summary}",
                )
                create_notification(db, ai_notification)

                logger.info(f"AI recommendations added for ticket {new_ticket.ticket_id}: {len(ai_result.recommended_parts)} parts")
            else:
                logger.warning(f"No AI recommendations found for ticket {new_ticket.ticket_id}")

        except Exception as ai_error:
            logger.error(f"AI processing failed for ticket {new_ticket.ticket_id}: {ai_error}")
            # Continue without AI - don't fail the ticket creation

        # Regular notification
        notification = NotificationCreate(
            user_id=ticket.user_id,
            message=f"New ticket created: {ticket.issue_type}",
        )
        create_notification(db, notification)

        return new_ticket

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        db.rollback()
        raise e

def get_ticket(db: Session, ticket_id: int):
    """Get ticket by ID"""
    return db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 10):
    """Get tickets with pagination"""
    return db.query(Ticket).offset(skip).limit(limit).all()

def update_ticket_status(db: Session, ticket_id: int, status: str):
    """Update ticket status"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if ticket:
        ticket.status = status
        ticket.updated_at = datetime.now()
        db.commit()
        db.refresh(ticket)

        # Notify on status change
        notification = NotificationCreate(
            user_id=ticket.user_id,
            message=f"Ticket #{ticket_id} status updated to: {status}",
        )
        create_notification(db, notification)

        return ticket
    return None

async def get_ticket_ai_recommendations(db: Session, ticket_id: int):
    """
    Get AI recommendations for an existing ticket
    NEW function that uses your AI system
    """
    try:
        ticket = get_ticket(db, ticket_id)
        if not ticket:
            return {"error": "Ticket not found"}

        ai_request = AIRecommendationRequest(
            user_issue=ticket.issue_text,
            issue_type=ticket.issue_type,
            machine_series=getattr(ticket, 'machine_series', None),
            max_recommendations=10
        )

        ai_result = await kubota_ai_service.get_ai_recommendations(ai_request)

        return {
            "ticket_id": ticket_id,
            "issue_text": ticket.issue_text,
            "ai_recommendations": ai_result,
            "generated_at": datetime.now()
        }

    except Exception as e:
        logger.error(f"Failed to get AI recommendations for ticket {ticket_id}: {e}")
        return {"error": str(e)}
