from typing import TypedDict, List, Dict, Any, Optional , Union
from langgraph.graph import StateGraph, END
import json
import logging
from datetime import datetime
from openai import OpenAI

# Import your existing components
from .ticket_processor_adapted import AdaptedTicketProcessor
from .symptoms_generator import SymptomSuggestionService

# External dependencies
try:
    from langchain.tools import Tool
    from langchain.chat_models import ChatOpenAI
   
except ImportError:
    print("Warning: LangGraph dependencies not available. Install with: pip install langgraph langchain-openai")

logger = logging.getLogger(__name__)

# ======================= STATE DEFINITION =======================

class KubotaAIState(TypedDict):
    """State object that flows through the LangGraph workflow"""
    # Input
    user_issue: str
    machine_series: Optional[str]
    user_id: Optional[int]
    ticket_id: Optional[int]

    # Processing stages
    processed_symptoms: List[str]
    embedding_vector: Optional[List[float]]
    similar_cases: List[Dict[str, Any]]
    recommended_parts: List[Dict[str, Any]]
    confidence_scores: Dict[str, Union[float, str]]
    inventory_status: Dict[str, Any]

    # Output
    final_recommendations: List[Dict[str, Any]]
    explanation: str
    next_actions: List[str]
    workflow_stage: str
    processing_log: List[str]
    error_message: Optional[str]

# ======================= KUBOTA AI AGENT CLASS =======================

class KubotaPartsAIAgent:
    """
    LangGraph-based AI Agent for Kubota Parts Recommendations
    Integrates with your existing embedding and vector search system
    """

    def __init__(self):
        self.processor = AdaptedTicketProcessor()
        self.symptom_service = SymptomSuggestionService()
        self.llm = None  # Will be initialized if LangChain is available
        self.workflow = self._build_workflow()

        # Initialize LLM if available
        # Initialize LLM if available
        # if ChatOpenAI:
        #     try:
        #         self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        #     except Exception as e:
        #         logger.warning(f"OpenAI LLM not available, using fallback logic: {e}")
        # else:
        #     logger.warning("LangChain ChatOpenAI not installed, using fallback logic"))

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with all agent nodes"""

        workflow = StateGraph(KubotaAIState)

        # Define all the agent nodes
        workflow.add_node("symptom_analyzer", self.symptom_analyzer_node)
        workflow.add_node("embedding_generator", self.embedding_generator_node)
        workflow.add_node("similarity_searcher", self.similarity_searcher_node)
        workflow.add_node("parts_recommender", self.parts_recommender_node)
        workflow.add_node("inventory_checker", self.inventory_checker_node)
        workflow.add_node("confidence_evaluator", self.confidence_evaluator_node)
        workflow.add_node("recommendation_formatter", self.recommendation_formatter_node)

        # Define the workflow connections
        workflow.set_entry_point("symptom_analyzer")

        workflow.add_edge("symptom_analyzer", "embedding_generator")
        workflow.add_edge("embedding_generator", "similarity_searcher")
        workflow.add_edge("similarity_searcher", "parts_recommender")
        workflow.add_edge("parts_recommender", "inventory_checker")
        workflow.add_edge("inventory_checker", "confidence_evaluator")
        workflow.add_edge("confidence_evaluator", "recommendation_formatter")
        workflow.add_edge("recommendation_formatter", END)

        return workflow

    # ======================= AGENT NODES =======================

    def symptom_analyzer_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 1: Analyze and process user symptoms
        Uses your existing SymptomSuggestionService
        """
        try:
            state["workflow_stage"] = "symptom_analysis"
            state["processing_log"] = state.get("processing_log", [])
            state["processing_log"].append(f"Starting symptom analysis: {state['user_issue'][:100]}...")

            # Use your existing symptom suggestion service
            technical_symptoms = self.symptom_service.suggest_technical_symptoms(
                user_symptom=state["user_issue"],
                machine_type=state.get("machine_series") or ""
            )

            # Extract the processed symptoms
            processed_symptoms = []
            for symptom in technical_symptoms:
                processed_symptoms.append(symptom.get("technical_symptom", symptom.get("symptom", "")))

            # Fallback to original if no technical symptoms found
            if not processed_symptoms:
                processed_symptoms = [state["user_issue"]]

            state["processed_symptoms"] = processed_symptoms
            state["processing_log"].append(f"Generated {len(processed_symptoms)} processed symptoms")

            return state

        except Exception as e:
            logger.error(f"Error in symptom analyzer: {e}")
            state["error_message"] = f"Symptom analysis failed: {str(e)}"
            state["processed_symptoms"] = [state["user_issue"]]  # Fallback
            return state

    def embedding_generator_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 2: Generate embeddings for processed symptoms
        This is where your embeddings are actually created and used!
        """
        try:
            state["workflow_stage"] = "embedding_generation"
            state["processing_log"].append("Generating embeddings for symptom matching...")

            # Use OpenAI to generate embeddings (this is key!)
            client = OpenAI()

            # Combine processed symptoms into search text
            search_text = " ".join(state["processed_symptoms"])

            # Generate embedding using OpenAI (same as your existing system)
            response = client.embeddings.create(
                input=search_text,
                model="text-embedding-ada-002"
            )

            embedding_vector = response.data[0].embedding
            state["embedding_vector"] = embedding_vector
            state["processing_log"].append(f"Generated {len(embedding_vector)}-dimensional embedding vector")

            return state

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            state["error_message"] = f"Embedding generation failed: {str(e)}"
            state["embedding_vector"] = None
            return state

    def similarity_searcher_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 3: Use embeddings to find similar cases
        This integrates with your existing vector search system!
        """
        try:
            state["workflow_stage"] = "similarity_search"
            state["processing_log"].append("Searching for similar cases using vector similarity...")

            if not state.get("embedding_vector"):
                state["processing_log"].append("No embedding available, falling back to text search")
                # Fallback to your existing text-based search
                similar_cases = self.processor.find_similar_issues(
                    issue_text=state["user_issue"],
                    issue_type="general",
                    limit=10
                )
            else:
                # Use your vector search with the generated embedding
                # This is the key integration point with your existing system!
                similar_cases = self.processor.find_similar_issues(
                    issue_text=state["user_issue"],
                    limit=10,
                    min_cutoff=0.65
                )

            state["similar_cases"] = [dict(case) for case in similar_cases] if similar_cases else []
            state["processing_log"].append(f"Found {len(state['similar_cases'])} similar cases")


            return state

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            state["error_message"] = f"Similarity search failed: {str(e)}"
            state["similar_cases"] = []
            return state

    def parts_recommender_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 4: Extract and rank parts recommendations
        Uses your existing parts extraction logic
        """
        try:
            state["workflow_stage"] = "parts_recommendation"
            state["processing_log"].append("Extracting parts recommendations from similar cases...")

            if not state.get("similar_cases"):
                state["recommended_parts"] = []
                return state

            # Use your existing parts extraction method
            recommended_parts = self.processor.extract_recommended_parts(state["similar_cases"])

            # Format for LangGraph state
            formatted_parts = []
            for part in recommended_parts:
                formatted_parts.append({
                    "part_number": part.get("part_number", part.get("partnumber", "")),
                    "confidence": part.get("confidence", 0.0),
                    "frequency": part.get("frequency", 0),
                    "reasoning": part.get("reasoning", part.get("recommendedfrom", "Historical data")),
                    "source_cases": part.get("source_cases", [])
                })

            state["recommended_parts"] = formatted_parts
            state["processing_log"].append(f"Recommended {len(formatted_parts)} parts")

            return state

        except Exception as e:
            logger.error(f"Error in parts recommendation: {e}")
            state["error_message"] = f"Parts recommendation failed: {str(e)}"
            state["recommended_parts"] = []
            return state

    def inventory_checker_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 5: Check inventory availability for recommended parts
        """
        try:
            state["workflow_stage"] = "inventory_check"
            state["processing_log"].append("Checking inventory availability...")

            inventory_status = {
                "available_parts": [],
                "out_of_stock_parts": [],
                "low_stock_parts": [],
                "total_estimated_cost": 0.0
            }

            # Mock inventory check (integrate with your actual inventory system)
            for part in state.get("recommended_parts", []):
                part_number = part.get("part_number", "")
                if part_number:
                    # This would be a real database query in production
                    stock_info = {
                        "part_number": part_number,
                        "in_stock": True,  # Mock data
                        "quantity": 10,    # Mock data
                        "estimated_cost": 45.50  # Mock data
                    }
                    inventory_status["available_parts"].append(stock_info)
                    inventory_status["total_estimated_cost"] += stock_info["estimated_cost"]

            state["inventory_status"] = inventory_status
            state["processing_log"].append(f"Checked inventory for {len(state['recommended_parts'])} parts")

            return state

        except Exception as e:
            logger.error(f"Error checking inventory: {e}")
            state["inventory_status"] = {"error": str(e)}
            return state

    def confidence_evaluator_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 6: Evaluate confidence scores for the entire recommendation
        """
        try:
            state["workflow_stage"] = "confidence_evaluation"
            state["processing_log"].append("Evaluating recommendation confidence...")

            confidence_scores = {}

            # Calculate various confidence metrics
            similar_cases = state.get("similar_cases", [])
            recommended_parts = state.get("recommended_parts", [])

            # Average similarity score from cases
            if similar_cases:
                avg_similarity = sum(case.get("similarity_score", case.get("similarityscore", 0)) 
                                   for case in similar_cases) / len(similar_cases)
                confidence_scores["case_similarity"] = avg_similarity
            else:
                confidence_scores["case_similarity"] = 0.0

            # Parts recommendation confidence
            if recommended_parts:
                avg_part_confidence = sum(part.get("confidence", 0) for part in recommended_parts) / len(recommended_parts)
                confidence_scores["parts_confidence"] = avg_part_confidence
            else:
                confidence_scores["parts_confidence"] = 0.0

            # Overall system confidence
            confidence_scores["overall_confidence"] = (
                confidence_scores["case_similarity"] * 0.4 +
                confidence_scores["parts_confidence"] * 0.6
            )

            # Quality assessment
            if confidence_scores["overall_confidence"] > 0.8:
                confidence_scores["quality"] = "high"
            elif confidence_scores["overall_confidence"] > 0.6:
                confidence_scores["quality"] = "medium"
            else:
                confidence_scores["quality"] = "low"

            state["confidence_scores"] = confidence_scores
            state["processing_log"].append(f"Overall confidence: {confidence_scores['overall_confidence']:.2f}")

            return state

        except Exception as e:
            logger.error(f"Error evaluating confidence: {e}")
            state["confidence_scores"] = {"error": str(e)}
            return state

    def recommendation_formatter_node(self, state: KubotaAIState) -> KubotaAIState:
        """
        Node 7: Format final recommendations and explanations
        """
        try:
            state["workflow_stage"] = "formatting"
            state["processing_log"].append("Formatting final recommendations...")

            # Create final recommendations
            final_recommendations = []
            for part in state.get("recommended_parts", []):
                recommendation = {
                    "part_number": part.get("part_number", ""),
                    "confidence": part.get("confidence", 0.0),
                    "frequency": part.get("frequency", 0),
                    "reasoning": part.get("reasoning", ""),
                    "priority": "high" if part.get("confidence", 0) > 0.8 else "medium" if part.get("confidence", 0) > 0.6 else "low"
                }
                final_recommendations.append(recommendation)

            # Sort by confidence
            final_recommendations.sort(key=lambda x: x["confidence"], reverse=True)

            state["final_recommendations"] = final_recommendations

            # Generate explanation
            confidence = state.get("confidence_scores", {}).get("overall_confidence", 0)
            case_count = len(state.get("similar_cases", []))

            try:
              confidence = float(confidence)
            except (ValueError, TypeError):
              confidence = 0.0 

            explanation = f"""
            AI Analysis Complete:

            Issue: {state['user_issue']}
            Similar Cases Found: {case_count}
            Overall Confidence: {confidence:.2f}

            Based on analysis of {case_count} similar cases from your Kubota parts database,
            I've identified {len(final_recommendations)} recommended parts with 
            {confidence:.1%} confidence level.

            The recommendations are ranked by confidence score and frequency of use
            in similar repair scenarios.
            """

            state["explanation"] = explanation.strip()

            # Generate next actions
            next_actions = []
            if confidence > 0.8:
                next_actions.append("Proceed with high-confidence recommendations")
            elif confidence > 0.6:
                next_actions.append("Review recommendations with technician")
            else:
                next_actions.append("Gather more diagnostic information")

            if state.get("inventory_status", {}).get("out_of_stock_parts"):
                next_actions.append("Order out-of-stock parts")

            state["next_actions"] = next_actions
            state["workflow_stage"] = "completed"
            state["processing_log"].append("Workflow completed successfully")

            return state

        except Exception as e:
            logger.error(f"Error formatting recommendations: {e}")
            state["error_message"] = f"Formatting failed: {str(e)}"
            return state

    # ======================= MAIN PROCESSING METHOD =======================

    def process_issue(
        self, 
        user_issue: str, 
        machine_series: Optional[str] = None,
        user_id: Optional[int] = None,
        ticket_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method to process an issue through the LangGraph workflow
        """
        try:
            # Initialize state
            initial_state: KubotaAIState = {
                "user_issue": user_issue,
                "machine_series": machine_series,
                "user_id": user_id,
                "ticket_id": ticket_id,
                "processed_symptoms": [],
                "embedding_vector": None,
                "similar_cases": [],
                "recommended_parts": [],
                "confidence_scores": {},
                "inventory_status": {},
                "final_recommendations": [],
                "explanation": "",
                "next_actions": [],
                "workflow_stage": "initialized",
                "processing_log": [],
                "error_message": None
            }

            workflow_graph = self._build_workflow() 
            compiled_workflow = workflow_graph.compile()

            # Process through the workflow
            final_state = compiled_workflow.invoke(initial_state)
            
            # Safe state access function
            def get_state_value(key, default=None):
                if final_state is None:
                    return default
                return final_state.get(key, default)

            # Return formatted result
            return {
                "success": True,
                "workflow_completed": True,
                "user_issue": user_issue,
                "final_recommendations": get_state_value("final_recommendations", []),
                "explanation": get_state_value("explanation", ""),
                "confidence_scores": get_state_value("confidence_scores", {}),
                "similar_cases_count": len(get_state_value("similar_cases", []) or []),
                "inventory_status": get_state_value("inventory_status", {}),
                "next_actions": get_state_value("next_actions", []),
                "processing_log": get_state_value("processing_log", []),
                "embedding_used": get_state_value("embedding_vector") is not None,
                "error_message": get_state_value("error_message")
            }

        except Exception as e:
            logger.error(f"Error in LangGraph workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_issue": user_issue,
                "final_recommendations": [],
                "explanation": f"Workflow failed: {str(e)}",
                "embedding_used": False
            }

# ======================= GLOBAL INSTANCE =======================

# Create global instance
kubota_ai_agent = KubotaPartsAIAgent()

# ======================= USAGE EXAMPLE =======================

def demo_usage():
    """Demonstrate how the LangGraph agent uses embeddings"""

    print("LANGGRAPH AGENT DEMO")
    print("="*50)

    # Example issue
    test_issue = "My L3901 tractor hydraulic system has very low pressure when lifting implements"

    print(f"Processing issue: {test_issue}")
    print()

    # Process through LangGraph
    result = kubota_ai_agent.process_issue(
        user_issue=test_issue,
        machine_series="L3901HST"
    )

    print("🔍 PROCESSING RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Embeddings Used: {result['embedding_used']}")
    print(f"Similar Cases Found: {result['similar_cases_count']}")
    print(f"Confidence: {result.get('confidence_scores', {}).get('overall_confidence', 0):.2f}")
    print()

    print("🔧 RECOMMENDATIONS:")
    for i, rec in enumerate(result["final_recommendations"][:3], 1):
        print(f"{i}. {rec['part_number']} (Confidence: {rec['confidence']:.2f})")

    print()
    print("📝 EXPLANATION:")
    print(result["explanation"])

    return result

if __name__ == "__main__":
    demo_usage()
