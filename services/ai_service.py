import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# Import your existing AI components
from ai.ticket_processor_adapted import AdaptedTicketProcessor
from ai.langgraph_agent import KubotaPartsAIAgent
from ai.symptoms_generator import SymptomSuggestionService
from ai.vector_search import test_vector_search, check_vector_data

# Import schemas
from schemas.ai_schema import (
    AIRecommendationRequest, 
    AIRecommendationResponse, 
    SimilaritySearchRequest,
    PartRecommendation,
    SimilarCase,
    AISystemStatus
)

logger = logging.getLogger(__name__)

class KubotaAIService:
    """
    Main AI service that integrates all your existing AI components
    This is the bridge between your AI files and the FastAPI routes
    """

    def __init__(self):
        # Initialize your existing components
        self.ticket_processor = AdaptedTicketProcessor()
        self.langgraph_agent = KubotaPartsAIAgent() 
        self.symptom_service = SymptomSuggestionService()

        logger.info("KubotaAIService initialized with existing components")

    async def get_ai_recommendations(self, request: AIRecommendationRequest) -> AIRecommendationResponse:
        """
        Get AI-powered parts recommendations using your existing system
        """
        start_time = time.time()

        try:
            logger.info(f"Processing AI recommendation request: {request.user_issue[:50]}...")

            # Use your existing LangGraph agent for comprehensive processing
            agent_result = self.langgraph_agent.process_issue(
                user_issue=request.user_issue,
                machine_series=request.machine_series
            )

            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            if agent_result and agent_result.get('success', False):
                # Convert agent results to API response format
                recommended_parts = []
                for rec in agent_result.get('final_recommendations', []):
                    recommended_parts.append(PartRecommendation(
                        part_number=rec.get('part_number', ''),
                        confidence=rec.get('confidence', 0.0),
                        frequency=rec.get('frequency', 0),
                        reasoning=rec.get('reasoning', 'AI recommendation'),
                        source_cases=rec.get('source_cases', []),
                        estimated_quantity=rec.get('avg_quantity', 1.0)
                    ))

                # Convert similar cases
                similar_cases = []
                for case in agent_result.get('similar_cases', [])[:10]:
                    similar_cases.append(SimilarCase(
                        claim_id=case.get('claimid', ''),
                        series_name=case.get('seriesname'),
                        sub_assembly=case.get('subassembly'),
                        symptom_description=case.get('symptomcomments_clean'),
                        defect_description=case.get('defectcomments_clean'),
                        similarity_score=case.get('similarity_score', 0.0),
                        parts_used=[]  # Would extract from case data
                    ))

                return AIRecommendationResponse(
                    success=True,
                    user_issue=request.user_issue,
                    processing_time_ms=processing_time,
                    recommended_parts=recommended_parts,
                    similar_cases=similar_cases,
                    total_similar_cases=len(agent_result.get('similar_cases', [])),
                    avg_confidence=agent_result.get('confidence', 0.0),
                    search_method="langgraph_agent",
                    explanation=agent_result.get('explanation', 'AI analysis completed'),
                    next_steps=agent_result.get('next_actions', []),
                    embeddings_used=agent_result.get('embedding_used', False),
                    fallback_triggered=agent_result.get('fallback_used', False)
                )
            else:
                # Fallback to direct ticket processor
                return await self._fallback_recommendation(request, processing_time)

        except Exception as e:
            logger.error(f"Error in AI recommendations: {e}")
            processing_time = (time.time() - start_time) * 1000
            return AIRecommendationResponse(
                success=False,
                user_issue=request.user_issue,
                processing_time_ms=processing_time,
                recommended_parts=[],
                similar_cases=[],
                total_similar_cases=0,
                avg_confidence=0.0,
                search_method="error",
                explanation=f"Processing failed: {str(e)}",
                embeddings_used=False,
                fallback_triggered=True
            )

    async def _fallback_recommendation(
            self, request: AIRecommendationRequest, processing_time: float) -> AIRecommendationResponse:
            """Fallback using direct ticket processor"""
            try:
                # Use your existing ticket processor directly
                similar_issues = self.ticket_processor.find_similar_issues(
                    issue_text=request.user_issue,
                    issue_type=request.machine_series,
                    limit=10,
                    min_cutoff=request.min_confidence
                )

                # Initialize lists
                recommended_parts: list[PartRecommendation] = []
                similar_cases: list[SimilarCase] = []

                if similar_issues:
                    # Extract parts recommendations
                    parts_recommendations = self.ticket_processor.extract_recommended_parts(similar_issues)

                    for part in parts_recommendations[:request.max_recommendations]:
                        recommended_parts.append(PartRecommendation(
                            part_number=part.get('partnumber', part.get('part_number', '')),
                            confidence=part.get('confidence', 0.5),
                            frequency=part.get('frequency', 1),
                            reasoning=part.get('recommendedfrom', 'Similarity search'),
                            estimated_quantity=part.get('avgquantity', 1.0)
                        ))

                    # Build similar cases list
                    for case in similar_issues[:10]:
                        similar_cases.append(SimilarCase(
                            claim_id=case.get("claimid", ""),
                            series_name=case.get("seriesname", ""),
                            sub_assembly=case.get("subassembly", ""),
                            symptom_description=case.get("symptomcomments_clean", ""),
                            defect_description=case.get("defectcomments_clean", ""),
                            similarity_score=case.get("similarity_score", 0.0),
                        ))

                    return AIRecommendationResponse(
                        success=True,
                        user_issue=request.user_issue,
                        processing_time_ms=processing_time,
                        recommended_parts=recommended_parts,
                        similar_cases=similar_cases,
                        total_similar_cases=len(similar_issues),
                        avg_confidence=sum(r.confidence for r in recommended_parts) / len(recommended_parts) if recommended_parts else 0,
                        search_method="fallback_processor",
                        explanation="Used fallback similarity search",
                        embeddings_used=True,
                        fallback_triggered=True
                    )
                else:
                    return AIRecommendationResponse(
                        success=False,
                        user_issue=request.user_issue,
                        processing_time_ms=processing_time,
                        recommended_parts=[],
                        similar_cases=[],
                        total_similar_cases=0,
                        avg_confidence=0.0,
                        search_method="no_results",
                        explanation="No similar cases found in database",
                        embeddings_used=False,
                        fallback_triggered=True
                    )
            except Exception as e:
                logger.error(f"Fallback recommendation failed: {e}")
                return AIRecommendationResponse(
                    success=False,
                    user_issue=request.user_issue,
                    processing_time_ms=processing_time,
                    recommended_parts=[],
                    similar_cases=[],
                    total_similar_cases=0,
                    avg_confidence=0.0,
                    search_method="error",
                    explanation=f"Fallback failed: {str(e)}",
                    embeddings_used=False,
                    fallback_triggered=True
                )


    async def similarity_search(self, request: SimilaritySearchRequest) -> Dict[str, Any]:
        """Perform similarity search using your existing vector search"""
        try:
            similar_issues = self.ticket_processor.find_similar_issues(
                issue_text=request.query_text,
                issue_type=request.series_filter,
                limit=request.max_results,
                min_cutoff=request.similarity_threshold
            )

            results = []
            for issue in similar_issues:
                results.append({
                    'claim_id': issue.get('claimid', ''),
                    'series': issue.get('seriesname', ''),
                    'assembly': issue.get('subassembly', ''),
                    'symptom': issue.get('symptomcomments_clean', ''),
                    'similarity_score': issue.get('similarity_score', 0.0)
                })

            return {
                'success': True,
                'query': request.query_text,
                'results': results,
                'total_found': len(results),
                'search_method': 'vector_embeddings'
            }

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return {
                'success': False,
                'query': request.query_text,
                'results': [],
                'total_found': 0,
                'error': str(e)
            }

    async def get_system_status(self) -> AISystemStatus:
        """Get AI system health status"""
        try:
            # Test vector search functionality
            vector_working = test_vector_search()

            # Get embedding statistics  
            check_vector_data()  # This prints stats, you might want to capture them

            return AISystemStatus(
                status="healthy" if vector_working else "degraded",
                embeddings_available=True,
                vector_search_working=vector_working,
                total_kubota_records=2000,  # You would query this from DB
                records_with_embeddings=1800,  # You would query this from DB
                embedding_coverage_percent=90.0,
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"System status check failed: {e}")
            return AISystemStatus(
                status="offline",
                embeddings_available=False,
                vector_search_working=False,
                total_kubota_records=0,
                records_with_embeddings=0,
                embedding_coverage_percent=0.0,
                last_updated=datetime.utcnow()
            )

    async def generate_technical_symptoms(self, user_symptom: str,  machine_type: Optional[str] = None) -> List[str]:
        """Generate technical symptom variations using your existing service"""
        try:
            suggestions = self.symptom_service.suggest_technical_symptoms(
                user_symptom=user_symptom,
                machine_type=machine_type or ""
            )

            return [s.get('technical_symptom', s.get('symptom', '')) for s in suggestions]

        except Exception as e:
            logger.error(f"Technical symptom generation failed: {e}")
            return [user_symptom]  # Fallback to original

# Global service instance
kubota_ai_service = KubotaAIService()
