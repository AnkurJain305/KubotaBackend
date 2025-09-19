from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Import your existing routes
from api.routes_user import router as user_router
from api.routes_machine import router as machine_router  
from api.routes_ticket import router as ticket_router
from api.routes_job import router as job_router
from api.routes_part import router as part_router
from api.routes_cause import router as cause_router
from api.routes_notify import router as notify_router

# Import new AI routes
from api.routes_ai import ai_router

# Database setup
from database import engine, get_db
from models.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Kubota Parts Management System with AI")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Test AI system on startup
    try:
        from services.ai_service import kubota_ai_service
        status = await kubota_ai_service.get_system_status()
        logger.info(f"🤖 AI System Status: {status.status}")
    except Exception as e:
        logger.warning(f"⚠️ AI system check failed: {e}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Kubota Parts Management System")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Kubota Parts Management System with AI",
    description="Complete parts management system with AI-powered recommendations using embeddings and vector search",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all your existing routes
app.include_router(user_router)
app.include_router(machine_router)
app.include_router(ticket_router)
app.include_router(job_router)
app.include_router(part_router)
app.include_router(cause_router)
app.include_router(notify_router)

# 🤖 Include NEW AI routes
app.include_router(ai_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Kubota Parts Management System with AI",
        "version": "2.0.0",
        "features": {
            "user_management": "✅ Available",
            "machine_tracking": "✅ Available", 
            "ticket_system": "✅ Available",
            "job_scheduling": "✅ Available",
            "parts_inventory": "✅ Available",
            "ai_recommendations": "🤖 AI-Powered",
            "vector_similarity": "🔍 Embeddings",
            "langgraph_agent": "🧠 Advanced AI"
        },
        "ai_endpoints": {
            "main_ai": "/ai/recommendations",
            "quick_ai": "/ai/recommendations/quick",
            "similarity_search": "/ai/similarity-search",
            "ai_test": "/ai/test",
            "ai_health": "/ai/health",
            "system_status": "/ai/system/status"
        },
        "documentation": "/docs",
        "admin_panel": "/admin" 
    }

# Health check endpoint
from sqlalchemy import text

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        from database import get_db
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {"database": db_status}



    # Test AI system
    try:
        from services.ai_service import kubota_ai_service
        ai_status = await kubota_ai_service.get_system_status()
        ai_health = ai_status.status
    except Exception as e:
        ai_health = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" and ai_health == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "ai_system": ai_health,
            "api": "healthy"
        },
        "endpoints_active": {
            "users": "✅",
            "machines": "✅",
            "tickets": "✅", 
            "jobs": "✅",
            "parts": "✅",
            "ai": "🤖✅" if ai_health == "healthy" else "🤖❌"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "available_endpoints": {
            "main": "/",
            "health": "/health",
            "docs": "/docs",
            "ai": "/ai/health"
        }
    }

@app.exception_handler(500) 
async def server_error_handler(request, exc):
    logger.error(f"Server error: {exc}")
    return {
        "error": "Internal server error",
        "message": "Please check system logs",
        "support": "Check /health endpoint for system status"
    }

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Kubota Parts Management System with AI")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
