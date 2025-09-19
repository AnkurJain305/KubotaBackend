from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.ticket import TicketCreate, TicketOut
from services.ticket_service import (
    create_ticket_with_ai,
    get_ticket,
    get_tickets, 
    update_ticket_status,
    get_ticket_ai_recommendations
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets with AI"])

@router.post("/", response_model=TicketOut)
async def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """
    Create ticket with automatic AI processing
    🤖 Enhanced with AI recommendations
    """
    try:
        # Use enhanced service that includes AI processing
        db_ticket = await create_ticket_with_ai(db, ticket)
        return db_ticket
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{ticket_id}", response_model=TicketOut)
async def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get ticket by ID"""
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket

@router.get("/", response_model=list[TicketOut])
async def list_tickets(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List tickets with pagination"""
    tickets = get_tickets(db, skip=skip, limit=limit)
    return tickets

@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: int, status: str, db: Session = Depends(get_db)):
    """Update ticket status"""
    ticket = update_ticket_status(db, ticket_id, status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

# 🤖 NEW AI ENDPOINTS FOR TICKETS

@router.get("/{ticket_id}/ai/recommendations")
async def get_ticket_recommendations(ticket_id: int, db: Session = Depends(get_db)):
    """
    🤖 Get AI-powered parts recommendations for a specific ticket
    Uses your existing AI system to analyze the ticket
    """
    try:
        result = await get_ticket_ai_recommendations(db, ticket_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI recommendations for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticket_id}/ai/similar")
async def get_similar_tickets(ticket_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """
    🔍 Find tickets similar to this one using AI
    """
    try:
        ticket = get_ticket(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Use AI service to find similar cases
        from services.ai_service import kubota_ai_service
        from schemas.ai_schema import SimilaritySearchRequest

        search_request = SimilaritySearchRequest(
            query_text=str(ticket.issue_text),
            max_results=limit
        )

        similar_cases = await kubota_ai_service.similarity_search(search_request)

        return {
            "ticket_id": ticket_id,
            "original_issue": ticket.issue_text,
            "similar_cases": similar_cases,
            "total_found": len(similar_cases.get("results", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar ticket search failed for {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ticket_id}/ai/analyze")
async def analyze_ticket_with_ai(ticket_id: int, db: Session = Depends(get_db)):
    """
    🧠 Full AI analysis of a ticket using LangGraph agent
    """
    try:
        ticket = get_ticket(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Use LangGraph agent for comprehensive analysis
        from ai.langgraph_agent import KubotaPartsAIAgent

        agent = KubotaPartsAIAgent()
        analysis = agent.process_issue(
            user_issue=str(ticket.issue_text),
            machine_series=None,  # You could get this from machine_id
            ticket_id=ticket_id
        )

        return {
            "ticket_id": ticket_id,
            "analysis": analysis,
            "analyzed_at": "2024-09-18T23:15:00Z"
        }

    except HTTPException:
        raise  
    except Exception as e:
        logger.error(f"AI analysis failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
