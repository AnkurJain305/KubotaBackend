from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from models.kubota_parts import KubotaPart, KubotaSeries, KubotaPartCatalog, SymptomRecommendation
from schemas.kubota_part import (
    KubotaPartCreate, KubotaPartUpdate, KubotaPartOut,
)
import json
import logging
from collections import Counter
import time
import numpy as np

logger = logging.getLogger(__name__)

class KubotaPartService:
    """Service class for Kubota parts operations"""

    def __init__(self):
        self.similarity_threshold = 0.65

    # ====================== KUBOTA PARTS CRUD ======================

    def create_kubota_part(self, db: Session, part_data: KubotaPartCreate)  -> Optional[KubotaPart]:
        """Create a new Kubota part entry"""
        try:
            db_part = KubotaPart(**part_data.dict())
            db.add(db_part)
            db.commit()
            db.refresh(db_part)
            return db_part
        except Exception as e:
            logger.error(f"Error creating Kubota part: {e}")
            db.rollback()
            return None

    def get_kubota_part(self, db: Session, claim_id: str) -> Optional[KubotaPart]:
        """Get Kubota part by claim ID"""
        return db.query(KubotaPart).filter(KubotaPart.claim_id == claim_id).first()

    def get_kubota_parts(self, db: Session, skip: int = 0, limit: int = 100) -> List[KubotaPart]:
        """Get list of Kubota parts with pagination"""
        return db.query(KubotaPart).offset(skip).limit(limit).all()

    def update_kubota_part(self, db: Session, claim_id: str, part_update: KubotaPartUpdate) -> Optional[KubotaPart]:
        """Update Kubota part by claim ID"""
        try:
            db_part = db.query(KubotaPart).filter(KubotaPart.claim_id == claim_id).first()
            if not db_part:
                return None

            update_data = part_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_part, field, value)

            db.commit()
            db.refresh(db_part)
            return db_part
        except Exception as e:
            logger.error(f"Error updating Kubota part {claim_id}: {e}")
            db.rollback()
            return None

    def delete_kubota_part(self, db: Session, claim_id: str) -> bool:
        """Delete Kubota part by claim ID"""
        try:
            db_part = db.query(KubotaPart).filter(KubotaPart.claim_id == claim_id).first()
            if not db_part:
                return False

            db.delete(db_part)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting Kubota part {claim_id}: {e}")
            db.rollback()
            return False

    # ====================== SEARCH FUNCTIONALITY ======================

    def search_kubota_parts(
        self, 
        db: Session, 
        search_term: Optional[str] = None,
        series_name: Optional[str] = None,
        sub_assembly: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search Kubota parts database"""
        try:
            query = db.query(KubotaPart)

            # Apply filters
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        KubotaPart.symptom_comments_clean.ilike(search_pattern),
                        KubotaPart.defect_comments_clean.ilike(search_pattern),
                        KubotaPart.part_name.ilike(search_pattern),
                        KubotaPart.sub_assembly.ilike(search_pattern)
                    )
                )

            if series_name:
                query = query.filter(KubotaPart.series_name.ilike(f"%{series_name}%"))

            if sub_assembly:
                query = query.filter(KubotaPart.sub_assembly.ilike(f"%{sub_assembly}%"))

            # Execute query
            parts = query.limit(limit).all()

            return {
                "success": True,
                "total_found": len(parts),
                "parts": [self._format_part_result(part) for part in parts]
            }

        except Exception as e:
            logger.error(f"Error searching Kubota parts: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_found": 0,
                "parts": []
            }

    # def vector_similarity_search(
    #     self, 
    #     db: Session, 
    #     search_request: SymptomSearchRequest
    # ) -> SymptomSearchResponse:
    #     """Perform vector similarity search using embeddings"""
    #     start_time = time.time()

    #     try:
    #         # First, get embedding for the search text (you'd integrate with OpenAI here)
    #         # For now, we'll use a placeholder approach

    #         # SQL query for vector similarity using pgvector
    #         similarity_query = text("""
    #             SELECT 
    #                 claim_id,
    #                 series_name,
    #                 sub_assembly,
    #                 symptom_comments_clean,
    #                 defect_comments_clean,
    #                 part_name,
    #                 part_dict,
    #                 1 - (embedding_symptom <=> :search_vector) as similarity_score
    #             FROM kubota_parts
    #             WHERE embedding_symptom IS NOT NULL
    #             AND 1 - (embedding_symptom <=> :search_vector) >= :min_similarity
    #             ORDER BY embedding_symptom <=> :search_vector
    #             LIMIT :limit
    #         """)

    #         # For demonstration, we'll use a simpler text-based approach
    #         # In production, you'd generate embeddings here
    #         parts = db.query(KubotaPart).filter(
    #             KubotaPart.symptom_comments_clean.ilike(f"%{search_request.symptom_text}%")
    #         ).limit(search_request.limit).all()

    #         results = []
    #         for part in parts:
    #             # Calculate similarity score (simplified)
    #             similarity = self._calculate_text_similarity(
    #                 search_request.symptom_text, 
    #                 part.symptom_comments_clean or ""
    #             )

    #             if similarity >= search_request.min_similarity:
    #                 part_recommendations = self._extract_part_numbers(part.part_dict)

    #                 results.append(SymptomSearchResult(
    #                     claim_id=part.claim_id,
    #                     series_name=part.series_name,
    #                     sub_assembly=part.sub_assembly,
    #                     symptom_description=part.symptom_comments_clean,
    #                     part_recommendations=part_recommendations,
    #                     similarity_score=similarity
    #                 ))

    #         # Sort by similarity score
    #         results.sort(key=lambda x: x.similarity_score, reverse=True)

    #         return SymptomSearchResponse(
    #             success=True,
    #             total_found=len(results),
    #             results=results,
    #             processing_time=time.time() - start_time
    #         )

    #     except Exception as e:
    #         logger.error(f"Error in vector similarity search: {e}")
    #         return SymptomSearchResponse(
    #             success=False,
    #             total_found=0,
    #             results=[],
    #             processing_time=time.time() - start_time
    #         )

    # def get_part_recommendations(
    #     self, 
    #     db: Session, 
    #     request: PartRecommendationRequest
    # ) -> PartRecommendationResponse:
    #     """Get AI-powered part recommendations"""
    #     start_time = time.time()

    #     try:
    #         # Search for similar cases
    #         similar_parts = db.query(KubotaPart).filter(
    #             KubotaPart.symptom_comments_clean.ilike(f"%{request.issue_description}%")
    #         ).all()

    #         if request.series_name:
    #             similar_parts = [p for p in similar_parts if p.series_name == request.series_name]

    #         if request.sub_assembly:
    #             similar_parts = [p for p in similar_parts if p.sub_assembly == request.sub_assembly]

    #         # Extract and count part occurrences
    #         part_counter = Counter()
    #         part_details = {}

    #         for part in similar_parts:
    #             if part.part_dict:
    #                 try:
    #                     part_data = json.loads(part.part_dict) if isinstance(part.part_dict, str) else part.part_dict
    #                     for part_num, quantity in part_data.items():
    #                         part_counter[part_num] += 1
    #                         if part_num not in part_details:
    #                             part_details[part_num] = {
    #                                 "name": part.part_name or "Unknown Part",
    #                                 "cases": []
    #                             }
    #                         part_details[part_num]["cases"].append(part.claim_id)
    #                 except:
    #                     pass

    #         # Generate recommendations
    #         recommendations = []
    #         total_cases = len(similar_parts)

    #         for part_num, frequency in part_counter.most_common(request.max_recommendations):
    #             confidence = frequency / total_cases if total_cases > 0 else 0

    #             if confidence >= request.confidence_threshold:
    #                 recommendations.append(PartRecommendationResult(
    #                     part_number=part_num,
    #                     part_name=part_details[part_num]["name"],
    #                     confidence=round(confidence, 3),
    #                     frequency=frequency,
    #                     reasoning=f"Recommended in {frequency} out of {total_cases} similar cases"
    #                 ))

    #         avg_confidence = sum(r.confidence for r in recommendations) / len(recommendations) if recommendations else 0

    #         return PartRecommendationResponse(
    #             success=True,
    #             recommendations=recommendations,
    #             similar_cases_count=total_cases,
    #             avg_confidence=round(avg_confidence, 3),
    #             processing_time=time.time() - start_time
    #         )

    #     except Exception as e:
    #         logger.error(f"Error getting part recommendations: {e}")
    #         return PartRecommendationResponse(
    #             success=False,
    #             recommendations=[],
    #             similar_cases_count=0,
    #             avg_confidence=0.0,
    #             processing_time=time.time() - start_time
    #         )

    # ====================== HELPER METHODS ======================

    def _format_part_result(self, part: KubotaPart) -> Dict[str, Any]:
        """Format KubotaPart for API response"""
        return {
            "claim_id": part.claim_id,
            "series_name": part.series_name,
            "sub_series": part.sub_series,
            "sub_assembly": part.sub_assembly,
            "symptom_description": part.symptom_comments_clean,
            "defect_description": part.defect_comments_clean,
            "part_name": part.part_name,
            "part_quantity": part.part_quantity,
            "has_embeddings": part.embedding_symptom is not None
        }

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation (replace with proper embedding similarity)"""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _extract_part_numbers(self, part_dict: Any) -> List[str]:
        """Extract part numbers from part_dict"""
        if not part_dict:
            return []

        try:
            if isinstance(part_dict, str):
                part_data = json.loads(part_dict)
            else:
                part_data = part_dict

            return list(part_data.keys()) if isinstance(part_data, dict) else []
        except:
            return []

    # ====================== STATISTICS ======================

    def get_kubota_statistics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive Kubota parts statistics"""
        try:
            # Basic counts
            total_parts = db.query(func.count(KubotaPart.claim_id)).scalar()
            parts_with_symptoms = db.query(func.count(KubotaPart.claim_id)).filter(
                KubotaPart.embedding_symptom.isnot(None)
            ).scalar()
            parts_with_defects = db.query(func.count(KubotaPart.claim_id)).filter(
                KubotaPart.embedding_defect.isnot(None)
            ).scalar()

            # Series distribution
            series_stats = db.query(
                KubotaPart.series_name, 
                func.count(KubotaPart.claim_id).label('count')
            ).group_by(KubotaPart.series_name).order_by(func.count(KubotaPart.claim_id).desc()).limit(10).all()

            # Assembly distribution
            assembly_stats = db.query(
                KubotaPart.sub_assembly, 
                func.count(KubotaPart.claim_id).label('count')
            ).filter(
                KubotaPart.sub_assembly.isnot(None)
            ).group_by(KubotaPart.sub_assembly).order_by(func.count(KubotaPart.claim_id).desc()).limit(10).all()

            return {
                "success": True,
                "statistics": {
                    "total_records": total_parts or 0,
                    "records_with_symptom_embeddings": parts_with_symptoms or 0,
                    "records_with_defect_embeddings": parts_with_defects or 0,
                    "embedding_coverage": {
                        "symptom_percentage": round((parts_with_symptoms / total_parts * 100), 2) if total_parts > 0 else 0,
                        "defect_percentage": round((parts_with_defects / total_parts * 100), 2) if total_parts > 0 else 0,
                    },
                    "top_series": [{"series": s[0] or "Unknown", "count": s[1]} for s in series_stats],
                    "top_assemblies": [{"assembly": a[0] or "Unknown", "count": a[1]} for a in assembly_stats]
                }
            }

        except Exception as e:
            logger.error(f"Error getting Kubota statistics: {e}")
            return {
                "success": False,
                "error": str(e),
                "statistics": {}
            }

# Global service instance
kubota_part_service = KubotaPartService()
