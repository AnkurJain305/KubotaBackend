from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

# Base schemas
class KubotaPartBase(BaseModel):
    claim_id: str = Field(..., description="Unique claim identifier")
    series_name: Optional[str] = None
    sub_series: Optional[str] = None
    sub_assembly: Optional[str] = None
    symptom_comments: Optional[str] = None
    defect_comments: Optional[str] = None
    symptom_comments_clean: Optional[str] = None
    defect_comments_clean: Optional[str] = None
    item_name: Optional[str] = None
    part_name: Optional[str] = None
    part_quantity: Optional[int] = None
    part_dict: Optional[Dict[str, Any]] = None

class KubotaPartCreate(KubotaPartBase):
    """Schema for creating new Kubota part entries"""
    pass

class KubotaPartUpdate(BaseModel):
    """Schema for updating Kubota part entries"""
    series_name: Optional[str] = None
    sub_series: Optional[str] = None
    sub_assembly: Optional[str] = None
    symptom_comments: Optional[str] = None
    defect_comments: Optional[str] = None
    symptom_comments_clean: Optional[str] = None
    defect_comments_clean: Optional[str] = None
    item_name: Optional[str] = None
    part_name: Optional[str] = None
    part_quantity: Optional[int] = None
    part_dict: Optional[Dict[str, Any]] = None

class KubotaPartOut(KubotaPartBase):
    """Schema for returning Kubota part data"""
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Series schemas
class KubotaSeriesBase(BaseModel):
    series_name: str = Field(..., description="Series name like L3901, M5-091")
    series_code: Optional[str] = None
    description: Optional[str] = None
    machine_type: Optional[str] = None

class KubotaSeriesCreate(KubotaSeriesBase):
    pass

class KubotaSeriesOut(KubotaSeriesBase):
    series_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Part catalog schemas
class KubotaPartCatalogBase(BaseModel):
    part_number: str = Field(..., description="Part number like 7J065-85200")
    part_name: str = Field(..., description="Part name")
    description: Optional[str] = None
    category: Optional[str] = None
    compatible_series: Optional[List[str]] = None
    price: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None

class KubotaPartCatalogCreate(KubotaPartCatalogBase):
    pass

class KubotaPartCatalogUpdate(BaseModel):
    part_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    compatible_series: Optional[List[str]] = None
    price: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None

class KubotaPartCatalogOut(KubotaPartCatalogBase):
    part_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# # Search and recommendation schemas
# class SymptomSearchRequest(BaseModel):
#     symptom_text: str = Field(..., description="User's symptom description")
#     series_name: Optional[str] = None
#     machine_type: Optional[str] = None
#     limit: int = Field(default=5, ge=1, le=20)
#     min_similarity: float = Field(default=0.65, ge=0.1, le=1.0)

# class SymptomSearchResult(BaseModel):
#     claim_id: str
#     series_name: Optional[str]
#     sub_assembly: Optional[str]
#     symptom_description: Optional[str]
#     part_recommendations: List[str]
#     similarity_score: float

# class SymptomSearchResponse(BaseModel):
#     success: bool
#     total_found: int
#     results: List[SymptomSearchResult]
#     processing_time: float

# class PartRecommendationRequest(BaseModel):
#     issue_description: str = Field(..., description="Description of the issue")
#     series_name: Optional[str] = None
#     sub_assembly: Optional[str] = None
#     confidence_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
#     max_recommendations: int = Field(default=10, ge=1, le=50)

# class PartRecommendationResult(BaseModel):
#     part_number: str
#     part_name: str
#     confidence: float
#     frequency: int
#     reasoning: str

# class PartRecommendationResponse(BaseModel):
#     success: bool
#     recommendations: List[PartRecommendationResult]
#     similar_cases_count: int
#     avg_confidence: float
#     processing_time: float
