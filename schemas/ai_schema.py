from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request schemas
class AIRecommendationRequest(BaseModel):
    """Request for AI parts recommendations"""
    user_issue: str = Field(..., description="Description of the issue")
    machine_series: Optional[str] = Field(None, description="Machine series (e.g., L3901)")
    issue_type: Optional[str] = Field(None, description="Type of issue (hydraulic, engine, etc.)")
    max_recommendations: int = Field(default=10, ge=1, le=20)
    min_confidence: float = Field(default=0.65, ge=0.1, le=1.0)

class SimilaritySearchRequest(BaseModel):
    """Request for similarity search"""
    query_text: str = Field(..., description="Text to search for")
    series_filter: Optional[str] = None
    assembly_filter: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.65, ge=0.1, le=1.0)

# Response schemas
class PartRecommendation(BaseModel):
    """Individual part recommendation"""
    part_number: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    frequency: int = Field(..., ge=0)
    reasoning: str
    source_cases: List[str] = Field(default_factory=list)
    estimated_quantity: float = Field(default=1.0)

class SimilarCase(BaseModel):
    """Similar case from database"""
    claim_id: str
    series_name: Optional[str]
    sub_assembly: Optional[str] 
    symptom_description: Optional[str]
    defect_description: Optional[str]
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    parts_used: List[str] = Field(default_factory=list)

class AIRecommendationResponse(BaseModel):
    """Response with AI recommendations"""
    success: bool
    request_id: Optional[str] = None
    user_issue: str
    processing_time_ms: float

    # Core results
    recommended_parts: List[PartRecommendation]
    similar_cases: List[SimilarCase]

    # Metadata
    total_similar_cases: int
    avg_confidence: float
    search_method: str = Field(description="embedding_search or text_fallback")

    # AI explanation
    explanation: str
    next_steps: List[str] = Field(default_factory=list)

    # System info
    embeddings_used: bool = False
    fallback_triggered: bool = False

class AISystemStatus(BaseModel):
    """AI system health status"""
    status: str = Field(description="healthy, degraded, or offline")
    embeddings_available: bool
    vector_search_working: bool
    total_kubota_records: int
    records_with_embeddings: int
    embedding_coverage_percent: float
    last_updated: datetime
