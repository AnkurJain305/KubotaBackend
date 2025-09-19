from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services.kubota_part_service import kubota_part_service
from schemas.kubota_part import (
    KubotaPartCreate, KubotaPartUpdate, KubotaPartOut,
    KubotaSeriesOut, KubotaPartCatalogOut
)

router = APIRouter(prefix="/kubota", tags=["Kubota Parts Intelligence"])

# ======================= KUBOTA PARTS CRUD =======================

@router.post("/parts/", response_model=KubotaPartOut)
def create_kubota_part(
    part: KubotaPartCreate,
    db: Session = Depends(get_db)
):
    """Create a new Kubota part entry"""
    db_part = kubota_part_service.create_kubota_part(db, part)
    if not db_part:
        raise HTTPException(status_code=400, detail="Failed to create Kubota part")
    return db_part

@router.get("/parts/{claim_id}", response_model=KubotaPartOut)
def get_kubota_part(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Get Kubota part by claim ID"""
    db_part = kubota_part_service.get_kubota_part(db, claim_id)
    if not db_part:
        raise HTTPException(status_code=404, detail="Kubota part not found")
    return db_part

@router.get("/parts/", response_model=List[KubotaPartOut])
def list_kubota_parts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List Kubota parts with pagination"""
    return kubota_part_service.get_kubota_parts(db, skip=skip, limit=limit)

@router.patch("/parts/{claim_id}", response_model=KubotaPartOut)
def update_kubota_part(
    claim_id: str,
    part_update: KubotaPartUpdate,
    db: Session = Depends(get_db)
):
    """Update Kubota part by claim ID"""
    db_part = kubota_part_service.update_kubota_part(db, claim_id, part_update)
    if not db_part:
        raise HTTPException(status_code=404, detail="Kubota part not found")
    return db_part

@router.delete("/parts/{claim_id}")
def delete_kubota_part(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Delete Kubota part by claim ID"""
    success = kubota_part_service.delete_kubota_part(db, claim_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kubota part not found")
    return {"message": f"Kubota part {claim_id} deleted successfully"}

# ======================= SEARCH & AI FEATURES =======================

@router.get("/parts/search/basic")
def search_kubota_parts(
    search_term: Optional[str] = Query(default=None, description="Search term for symptoms, parts, or assembly"),
    series_name: Optional[str] = Query(default=None, description="Filter by Kubota series"),
    sub_assembly: Optional[str] = Query(default=None, description="Filter by sub-assembly"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Basic text search across Kubota parts database"""
    return kubota_part_service.search_kubota_parts(
        db=db,
        search_term=search_term,
        series_name=series_name,
        sub_assembly=sub_assembly,
        limit=limit
    )

# @router.post("/ai/symptom-search", response_model=SymptomSearchResponse)
# def ai_symptom_search(
#     search_request: SymptomSearchRequest,
#     db: Session = Depends(get_db)
# ):
#     """AI-powered symptom similarity search using embeddings"""
#     return kubota_part_service.vector_similarity_search(db, search_request)

# @router.post("/ai/part-recommendations", response_model=PartRecommendationResponse)
# def get_ai_part_recommendations(
#     recommendation_request: PartRecommendationRequest,
#     db: Session = Depends(get_db)
# ):
#     """Get AI-powered parts recommendations for an issue"""
#     return kubota_part_service.get_part_recommendations(db, recommendation_request)

# @router.get("/ai/analyze-issue")
# def analyze_issue_with_kubota_ai(
#     issue_text: str = Query(..., description="Description of the issue"),
#     series_name: Optional[str] = Query(default=None, description="Kubota series name"),
#     confidence_threshold: float = Query(default=0.7, ge=0.1, le=1.0),
#     max_recommendations: int = Query(default=10, ge=1, le=50),
#     db: Session = Depends(get_db)
# ):
#     """
#     Comprehensive issue analysis with AI parts recommendations
#     This is the main endpoint for AI-powered diagnostics
#     """
#     # Create recommendation request
#     request = PartRecommendationRequest(
#         issue_description=issue_text,
#         series_name=series_name,
#         confidence_threshold=confidence_threshold,
#         max_recommendations=max_recommendations
#     )

#     # Get AI recommendations
#     recommendations = kubota_part_service.get_part_recommendations(db, request)

#     # Also get similar symptom cases
#     symptom_request = SymptomSearchRequest(
#         symptom_text=issue_text,
#         series_name=series_name,
#         limit=5
#     )
#     similar_cases = kubota_part_service.vector_similarity_search(db, symptom_request)

#     return {
#         "success": True,
#         "issue_analysis": {
#             "original_issue": issue_text,
#             "series_filter": series_name,
#             "confidence_threshold": confidence_threshold
#         },
#         "ai_recommendations": recommendations.dict(),
#         "similar_cases": similar_cases.dict(),
#         "summary": {
#             "total_recommendations": len(recommendations.recommendations),
#             "avg_confidence": recommendations.avg_confidence,
#             "similar_cases_found": similar_cases.total_found,
#             "processing_quality": "high" if recommendations.avg_confidence > 0.8 else "medium" if recommendations.avg_confidence > 0.6 else "low"
#         }
#     }

# ======================= STATISTICS & ANALYTICS =======================

@router.get("/statistics")
def get_kubota_statistics(db: Session = Depends(get_db)):
    """Get comprehensive Kubota parts database statistics"""
    return kubota_part_service.get_kubota_statistics(db)

@router.get("/health")
def kubota_system_health():
    """Health check for Kubota parts system"""
    return {
        "status": "healthy",
        "system": "kubota-parts-ai",
        "features": {
            "embedding_search": True,
            "ai_recommendations": True,
            "vector_similarity": True,
            "parts_catalog": True
        },
        "endpoints": {
            "basic_search": "/kubota/parts/search/basic",
            "ai_symptom_search": "/kubota/ai/symptom-search",
            "ai_recommendations": "/kubota/ai/part-recommendations",
            "issue_analysis": "/kubota/ai/analyze-issue",
            "statistics": "/kubota/statistics"
        }
    }

# ======================= SERIES & CATALOG INFO =======================

@router.get("/series/")
def list_kubota_series(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100)
):
    """List available Kubota series"""
    from models.kubota_parts import KubotaSeries
    series_list = db.query(KubotaSeries).offset(skip).limit(limit).all()
    return {
        "success": True,
        "total_series": len(series_list),
        "series": [
            {
                "series_id": s.series_id,
                "series_name": s.series_name,
                "series_code": s.series_code,
                "description": s.description,
                "machine_type": s.machine_type
            }
            for s in series_list
        ]
    }

@router.get("/catalog/parts")
def get_parts_catalog(
    category: Optional[str] = Query(default=None, description="Filter by part category"),
    series_compatible: Optional[str] = Query(default=None, description="Filter by compatible series"),
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500)
):
    """Get Kubota parts catalog with filters"""
    from models.kubota_parts import KubotaPartCatalog
    from sqlalchemy import and_

    query = db.query(KubotaPartCatalog)

    if category:
        query = query.filter(KubotaPartCatalog.category.ilike(f"%{category}%"))

    if series_compatible:
        query = query.filter(KubotaPartCatalog.compatible_series.contains([series_compatible]))

    catalog_parts = query.offset(skip).limit(limit).all()

    return {
        "success": True,
        "filters_applied": {
            "category": category,
            "series_compatible": series_compatible
        },
        "total_found": len(catalog_parts),
        "parts": [
            {
                "part_id": p.part_id,
                "part_number": p.part_number,
                "part_name": p.part_name,
                "description": p.description,
                "category": p.category,
                "compatible_series": p.compatible_series,
            }
            for p in catalog_parts
        ]
    }

# ======================= DEMO ENDPOINTS =======================

@router.get("/demo/sample-issues")
def get_sample_issues():
    """Get sample issues for testing the AI system"""
    return {
        "sample_issues": [
            {
                "issue": "hydraulic fluid leaking from quick coupler",
                "series": "L3901HST",
                "expected_parts": ["7J065-85200", "9L200-54321"]
            },
            {
                "issue": "engine running rough with black smoke",
                "series": "M5-091", 
                "expected_parts": ["2L455-99888", "1A111-22333"]
            },
            {
                "issue": "HST transmission overheating and making noise",
                "series": "B2650HSD",
                "expected_parts": ["5N777-88999", "3P888-11222"]
            },
            {
                "issue": "loader hydraulic system very slow",
                "series": "L4701HST",
                "expected_parts": ["7J065-85200", "8K110-12345"]
            },
            {
                "issue": "engine hard to start fuel warning light",
                "series": "M5-111",
                "expected_parts": ["1A111-22333", "4K123-55667"]
            }
        ],
        "usage": "Use these sample issues to test the AI recommendation system at /kubota/ai/analyze-issue"
    }
