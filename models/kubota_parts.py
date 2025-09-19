from sqlalchemy import Column, String, Text, Integer, ARRAY, Float, DateTime, JSON
from .base import Base
from sqlalchemy import TIMESTAMP, func
from datetime import datetime

class KubotaPart(Base):
    """KubotaPart model for storing Kubota parts data with embeddings"""
    __tablename__ = "kubota_parts"

    # Primary key
    claimid = Column(String(50), primary_key=True, index=True)

    # Basic part information  
    seriesname = Column(String(20))
    subseries = Column(String(20))
    subassembly = Column(String(100))

    # Issue descriptions
    symptomcomments = Column(Text)
    defectcomments = Column(Text)
    symptomcomments_clean = Column(Text)
    defectcomments_clean = Column(Text)

    # Part details
    itemname = Column(String(100))
    partname = Column(String(100))
    partquantity = Column(String(20))
    partdict = Column(JSON)  # Store parts as JSON

    # AI EMBEDDINGS - This is the key addition!
    embedding_symptom_vector = Column(ARRAY(Float))  # 1536-dim embeddings
    embedding_defect_vector = Column(ARRAY(Float))   # 1536-dim embeddings

    # Metadata

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<KubotaPart(claimid='{self.claimid}', series='{self.seriesname}')>"


class KubotaSeries(Base):
    """Kubota machine series reference table"""
    __tablename__ = "kubota_series"

    series_id = Column(Integer, primary_key=True, index=True)
    series_name = Column(String, unique=True, nullable=False)
    series_code = Column(String, unique=True, nullable=True)
    description = Column(Text, nullable=True)
    machine_type = Column(String, nullable=True)  # tractor, loader, mower, etc.
    created_at = Column(TIMESTAMP, server_default=func.now())

class KubotaPartCatalog(Base):
    """Kubota parts catalog for reference"""
    __tablename__ = "kubota_part_catalog"

    part_id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, unique=True, nullable=False, index=True)
    part_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # hydraulic, engine, transmission, etc.
    compatible_series = Column(ARRAY(String), nullable=True)  # Which series this part fits
    price = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SymptomRecommendation(Base):
    """AI-generated symptom recommendations"""
    __tablename__ = "symptom_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_symptom = Column(Text, nullable=False)
    recommended_symptom = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    source = Column(String, nullable=True)  # AI, historical, manual
    usage_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
