from openai import OpenAI
from ai.ticket_processor_adapted import AdaptedTicketProcessor
import json
from typing import List, Dict
import re

client = OpenAI()

class SymptomSuggestionService:
    def __init__(self):
        self.processor = AdaptedTicketProcessor()

    def suggest_technical_symptoms(self, user_symptom: str, machine_type: str = None or "") -> List[Dict]:
        """
        Convert user symptom to technical symptom suggestions

        Args:
            user_symptom (str): User's plain language symptom description
            machine_type (str): Machine type for context (BX, L, M series)

        Returns:
            List[Dict]: List of technical symptom suggestions with confidence
        """
        try:
            # Get similar symptoms from historical data
            historical_suggestions = self._get_historical_symptom_suggestions(user_symptom, machine_type)

            # Use OpenAI to generate technical variations
            ai_suggestions = self._generate_ai_symptom_suggestions(user_symptom, machine_type)

            # Combine and rank suggestions
            combined_suggestions = self._combine_and_rank_suggestions(
                historical_suggestions, 
                ai_suggestions
            )

            return combined_suggestions[:5]  # Top 5 suggestions

        except Exception as e:
            print(f"Error generating symptom suggestions: {e}")
            return [{"suggestion": user_symptom, "confidence": 1.0, "source": "original"}]

    def _get_historical_symptom_suggestions(self, user_symptom: str, machine_type: str) -> List[Dict]:
        """Get similar symptoms from historical kubota_parts data"""
        try:
            # Search for similar symptoms in historical data
            similar_cases = self.processor.find_similar_issues(
                user_symptom, 
                machine_type, 
                limit=10
            )

            suggestions = []
            seen_symptoms = set()

            for case in similar_cases:
                # Extract clean symptoms
                if case['symptomcomments_clean'] and case['symptomcomments_clean'] not in seen_symptoms:
                    suggestions.append({
                        "suggestion": case['symptomcomments_clean'][:100],  # Limit length
                        "confidence": case['similarity_score'],
                        "source": "historical",
                        "series": case['seriesname'],
                        "subassembly": case['subassembly']
                    })
                    seen_symptoms.add(case['symptomcomments_clean'])

            return suggestions[:3]  # Top 3 historical suggestions

        except Exception as e:
            print(f"Error getting historical suggestions: {e}")
            return []

    def _generate_ai_symptom_suggestions(self, user_symptom: str, machine_type: str) -> List[Dict]:
        """Generate technical symptom variations using OpenAI"""
        try:
            machine_context = f" for {machine_type} series equipment" if machine_type else ""

            prompt = f"""
            Convert this user symptom description into 3 technical symptom variations that a technician would understand{machine_context}:

            User symptom: "{user_symptom}"

            Provide 3 technical variations that are:
            1. More specific and technical
            2. Include relevant system/component names
            3. Use proper technical terminology

            Return as JSON array:
            [
                {{"suggestion": "technical symptom 1", "confidence": 0.9}},
                {{"suggestion": "technical symptom 2", "confidence": 0.8}},
                {{"suggestion": "technical symptom 3", "confidence": 0.7}}
            ]
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            ai_suggestions_raw = response.choices[0].message.content

            # Parse JSON response
            try:
                ai_suggestions_json = json.loads(ai_suggestions_raw) if ai_suggestions_raw else []
                return [
                    {
                        **suggestion,
                        "source": "ai_generated"
                    }
                    for suggestion in ai_suggestions_json
                ]
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [{
                    "suggestion": user_symptom,
                    "confidence": 0.5,
                    "source": "ai_fallback"
                }]

        except Exception as e:
            print(f"Error generating AI suggestions: {e}")
            return []

    def _combine_and_rank_suggestions(self, historical: List[Dict], ai_generated: List[Dict]) -> List[Dict]:
        """Combine and rank all suggestions by confidence and diversity"""
        all_suggestions = historical + ai_generated

        # Remove duplicates and rank by confidence
        unique_suggestions = {}
        for suggestion in all_suggestions:
            text = suggestion['suggestion'].lower().strip()
            if text not in unique_suggestions:
                unique_suggestions[text] = suggestion
            elif suggestion['confidence'] > unique_suggestions[text]['confidence']:
                unique_suggestions[text] = suggestion

        # Sort by confidence descending
        ranked_suggestions = sorted(
            unique_suggestions.values(),
            key=lambda x: x['confidence'],
            reverse=True
        )

        return ranked_suggestions

    def process_image_symptom(self, image_data: bytes, image_format: str = "jpeg") -> str:
        """
        Process image to extract symptom description using OpenAI Vision

        Args:
            image_data (bytes): Image binary data
            image_format (str): Image format (jpeg, png, etc.)

        Returns:
            str: Extracted symptom description
        """
        try:
            import base64

            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and describe any mechanical issues, symptoms, or problems visible. Focus on equipment malfunctions, damage, or abnormal conditions that would require repair. Provide a technical description suitable for a maintenance ticket."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            print(f"Error processing image symptom: {e}")
            return "Unable to process image. Please provide text description."