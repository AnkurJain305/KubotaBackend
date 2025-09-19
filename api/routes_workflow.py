from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from database import get_db
from schemas.inventory import TicketProcessingRequest, TicketProcessingResponse

router = APIRouter(prefix="/api/workflow", tags=["AI Workflow"])

@router.post("/process-ticket", response_model=TicketProcessingResponse)
async def process_ticket_with_ai(
    request: TicketProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """🤖 MAIN AI WORKFLOW - LangGraph Agent Processing"""
    try:
        # Import the AI agent
        from ai.langgraph_agent import kubota_agent

        if kubota_agent is None:
            # Fallback to basic ticket creation
            from services.ticket_service import create_ticket
            from schemas.ticket import TicketCreate

            ticket_create = TicketCreate(
                issue_text=request.user_symptom,
                machine_id=request.machine_id,
                user_id=request.user_id,
                priority=request.priority
            )

            new_ticket = create_ticket(db, ticket_create)

            return TicketProcessingResponse(
                success=True,
                ticket_id=new_ticket.ticket_id if new_ticket else None,
                selected_symptom=request.user_symptom,
                suggested_symptoms=[{"suggestion": request.user_symptom, "confidence": 0.8, "category": "general"}],
                parts_recommendations=[],
                repair_scheduled=False,
                parts_available=False,
                notifications_sent=["ticket_created"],
                processing_time=1.0,
                agent_messages=["Ticket created using basic processing"]
            )

        # Process with LangGraph agent
        result = await kubota_agent.process_ticket({
            "user_symptom": request.user_symptom,
            "user_id": request.user_id,
            "machine_id": request.machine_id,
            "machine_type": request.machine_type,
            "priority": request.priority
        })

        return TicketProcessingResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@router.get("/ticket/{ticket_id}/status")
async def get_workflow_status(ticket_id: int, db: Session = Depends(get_db)):
    """Get complete workflow status"""
    from models.ticket import Ticket
    from models.part import PartsRequest

    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    parts_requests = db.query(PartsRequest).filter(
        PartsRequest.ticket_id == ticket_id
    ).all()

    return {
        "ticket_id": ticket_id,
        "current_status": ticket.status,
        "workflow_stage": "completed" if ticket.status == "completed" else "in_progress",
        "parts_status": {
            "total_requested": len(parts_requests),
            "available": sum(1 for req in parts_requests if req.status == "approved"),
            "unavailable": sum(1 for req in parts_requests if req.status != "approved")
        }
    }

@router.get("/dashboard/overview")
async def get_workflow_dashboard(db: Session = Depends(get_db)):
    """System dashboard metrics"""
    from sqlalchemy import func
    from models.ticket import Ticket
    from models.part import PartsRequest

    open_tickets = db.query(func.count(Ticket.ticket_id)).filter(Ticket.status == "open").scalar()
    total_parts = db.query(func.count(PartsRequest.id)).scalar()

    return {
        "open_tickets": open_tickets or 0,
        "total_parts_requests": total_parts or 0,
        "system_health": "operational",
        "ai_agent_status": "available"
    }
