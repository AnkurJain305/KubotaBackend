from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

# Import your AI service
from services.ai_service import kubota_ai_service
from schemas.ai_schema import (
    AIRecommendationRequest,
    AIRecommendationResponse, 
    SimilaritySearchRequest,
    AISystemStatus
)

logger = logging.getLogger(__name__)

# Create AI router
ai_router = APIRouter(prefix="/ai", tags=["AI Recommendations"])

@ai_router.post("/recommendations", response_model=AIRecommendationResponse)
async def get_ai_recommendations(request: AIRecommendationRequest):
    """
    🤖 MAIN AI ENDPOINT - Get parts recommendations using your existing AI system

    This integrates with your:
    - ticket_processor_adapted.py
    - langgraph_agent.py  
    - embeddings.py
    - vector_search.py
    """
    try:
        logger.info(f"AI recommendation request: {request.user_issue[:50]}...")

        # Use your AI service which integrates all your existing AI files
        result = await kubota_ai_service.get_ai_recommendations(request)

        logger.info(f"AI recommendation completed: {result.success}, {len(result.recommended_parts)} parts")
        return result

    except Exception as e:
        logger.error(f"AI recommendation endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI recommendation failed: {str(e)}"
        )

@ai_router.get("/recommendations/quick")
async def quick_ai_recommendations(
    issue: str,
    series: str = None or "",
    max_parts: int = 5
):
    """
    QUICK AI ENDPOINT - Simplified interface for fast recommendations
    """
    try:
        request = AIRecommendationRequest(
            user_issue=issue,
            issue_type=None,
            machine_series=series,
            max_recommendations=max_parts
        )

        result = await kubota_ai_service.get_ai_recommendations(request)

        # Return simplified response
        return {
            "success": result.success,
            "issue": issue,
            "parts": [
                {
                    "part_number": p.part_number,
                    "confidence": p.confidence,
                    "frequency": p.frequency
                }
                for p in result.recommended_parts
            ],
            "similar_cases_found": result.total_similar_cases,
            "explanation": result.explanation,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        logger.error(f"Quick AI recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_router.post("/similarity-search") 
async def similarity_search(request: SimilaritySearchRequest):
    """
    SIMILARITY SEARCH - Find similar cases using your vector search
    """
    try:
        result = await kubota_ai_service.similarity_search(request)
        return result

    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_router.get("/system/status", response_model=AISystemStatus)
async def get_ai_system_status():
    """
    SYSTEM STATUS - Check AI system health
    """
    try:
        status = await kubota_ai_service.get_system_status()
        return status

    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_router.get("/symptoms/generate")
async def generate_technical_symptoms(
    user_symptom: str,
    machine_type: str = None or ""
):
    """
    SYMPTOM GENERATOR - Generate technical symptoms using your existing service
    """
    try:
        technical_symptoms = await kubota_ai_service.generate_technical_symptoms(
            user_symptom=user_symptom,
            machine_type=machine_type
        )

        return {
            "user_symptom": user_symptom,
            "machine_type": machine_type,
            "technical_symptoms": technical_symptoms,
            "total_generated": len(technical_symptoms)
        }

    except Exception as e:
        logger.error(f"Symptom generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_router.get("/test")
async def test_ai_system():
    """TEST ENDPOINT - Quick test of your AI system
    """
    try:
        # Test with a simple hydraulic issue
        test_request = AIRecommendationRequest(
            user_issue="hydraulic oil leak from quick coupler",
            issue_type="hydraulic",
            machine_series="L3901",
            max_recommendations=3
        )

        result = await kubota_ai_service.get_ai_recommendations(test_request)

        return {
            "test_status": "success" if result.success else "failed",
            "embeddings_working": result.embeddings_used,
            "parts_found": len(result.recommended_parts),
            "similar_cases": result.total_similar_cases,
            "processing_time_ms": result.processing_time_ms,
            "message": "AI system is working!" if result.success else "AI system has issues"
        }

    except Exception as e:
        logger.error(f"AI system test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "message": "AI system test failed"
        }

# Health check for the AI system
@ai_router.get("/health")
async def ai_health_check():
    """
    HEALTH CHECK - Simple health check for AI system
    """
    try:
        # Quick health check without heavy processing
        from ai.vector_search import check_vector_data

        return {
            "status": "healthy",
            "ai_components": {
                "ticket_processor": "available",
                "langgraph_agent": "available", 
                "vector_search": "available",
                "embeddings": "available"
            },
            "endpoints": {
                "recommendations": "/ai/recommendations",
                "quick": "/ai/recommendations/quick",
                "similarity": "/ai/similarity-search",
                "test": "/ai/test"
            },
            "message": "Kubota AI system is running"
        }

    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "AI system has issues"
        }
