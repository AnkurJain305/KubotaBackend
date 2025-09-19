from typing import Optional, Dict, Any, List
from datetime import datetime
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as PGConnection
import logging
import json
from openai import OpenAI
from .db_utils import connect_to_database
from psycopg2.extensions import cursor as PGCursor

client = OpenAI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AdaptedTicketProcessor:
    def __init__(self):
        self.conn: Optional[PGConnection] = None

    def connect_to_database(self) -> bool:
        """Connect to PostgreSQL database"""
        self.conn = connect_to_database()  # make sure this returns a psycopg2 connection
        return self.conn is not None

    def disconnect(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_ticket(self, ticket_data: Dict[str, Any]) -> Optional[int]:
        """Create a new ticket using your schema"""
        if not self.connect_to_database() or self.conn is None:
            logger.error("Database connection is not established")
            return None

        cursor: Optional[RealDictCursor] = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                INSERT INTO tickets (
                    issue_type, issue_text, status, machine_id, user_id, created_at
                ) VALUES (
                    %(issue_type)s, %(issue_text)s, %(status)s, 
                    %(machine_id)s, %(user_id)s, %(created_at)s
                ) RETURNING ticket_id, created_at
                """,
                {
                    'issue_type': ticket_data.get('issue_type'),
                    'issue_text': ticket_data.get('issue_text'),
                    'status': ticket_data.get('status', 'open'),
                    'machine_id': ticket_data.get('machine_id'),
                    'user_id': ticket_data.get('user_id'),
                    'created_at': ticket_data.get('created_at', datetime.now())
                }
            )

            result = cursor.fetchone()
            if not result:
                logger.error("Ticket creation failed: No ID returned")
                return None

            ticket_id = result['ticket_id']
            self.conn.commit()
            logger.info(f"Ticket created: ID {ticket_id}")
            return ticket_id

        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            if self.conn:
                self.conn.rollback()
            return None

        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    # ---------------- Embedding Generator ----------------
    def generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI (same as used in DB)."""
        if not text:
            return [0.0] * 1536  # fallback (OpenAI ada-002 has 1536 dims)

        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    # ---------------- Find Similar Issues ----------------
    def find_similar_issues(
        self,
        issue_text: str,
        issue_type: Optional[str] = None,
        limit: int = 5,
        alpha: float = 0.7,
        min_cutoff: float = 0.65
    ) -> List[Dict[str, Any]]:
        """Find similar issues using pgvector hybrid search with fallbacks"""
        if not self.connect_to_database() or self.conn is None:
            return []

        cursor: Optional[RealDictCursor] = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            query_embedding = self.generate_openai_embedding(issue_text)
            if not query_embedding:
                return []

            def run_query(alpha_value: float, with_type: bool = True) -> List[Dict[str, Any]]:
                query = """
                    SELECT 
                        claimid, seriesname, subseries, subassembly,
                        symptomcomments, defectcomments, 
                        symptomcomments_clean, defectcomments_clean,
                        partname, partquantity,
                        (
                            %s * (1 - (embedding_symptom_vector <=> %s::vector)) +
                            %s * (1 - (embedding_defect_vector <=> %s::vector))
                        ) AS similarity_score
                    FROM kubota_parts
                    WHERE embedding_symptom_vector IS NOT NULL
                    AND embedding_defect_vector IS NOT NULL
                """
                params: List[Any] = [alpha_value, query_embedding, 1 - alpha_value, query_embedding]

                if with_type and issue_type:
                    query += " AND (seriesname ILIKE %s OR subassembly ILIKE %s)"
                    params.extend([f"%{issue_type}%", f"%{issue_type}%"])

                query += " ORDER BY similarity_score DESC LIMIT %s"
                params.append(20)  # expand candidate pool

                cursor.execute(query, params)
                rows = cursor.fetchall()  
                return [dict(row) for row in rows]  # ✅ cast each row to dict


            rows = run_query(alpha, True)
            if not rows:
                rows = run_query(0.5, True)
            if not rows and issue_type:
                rows = run_query(alpha, False)
            if not rows:
                rows = run_query(0.5, False)

            filtered = [r for r in rows if r.get("similarity_score", 0.0) >= min_cutoff]
            return filtered[:limit]

        except Exception as e:
            logger.error(f"Error finding similar issues: {e}")
            return []

        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    # ---------------- Recommended Parts ----------------
    def extract_recommended_parts(self, similar_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract recommended parts from similar cases"""
        parts_frequency: Dict[str, int] = {}
        total_cases = len(similar_cases)

        for case in similar_cases:
            part_str = case.get('partname', '')
            if part_str:
                for part in map(str.strip, str(part_str).split(',')):
                    if part and part.lower() != 'nan':
                        parts_frequency[part] = parts_frequency.get(part, 0) + 1

        recommendations: List[Dict[str, Any]] = []
        for part, frequency in sorted(parts_frequency.items(), key=lambda x: x[1], reverse=True):
            confidence = frequency / total_cases if total_cases else 0
            recommendations.append({
                'part_number': part,
                'frequency': frequency,
                'confidence': round(confidence, 3),
                'recommended_from': f"{frequency}/{total_cases} similar cases"
            })
        return recommendations[:10]

    def save_recommendations(
        self,
        ticket_id: int,
        similar_cases: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """Save recommendations to database"""
        if not self.connect_to_database() or self.conn is None:
            return False

        
        cursor: Optional[PGCursor] = None
        try:
            cursor = self.conn.cursor()
            analysis_notes = {
                'total_similar_cases': len(similar_cases),
                'avg_similarity': sum(case.get('similarity_score', 0.0) for case in similar_cases) / len(similar_cases) if similar_cases else 0,
                'issue_types_found': list({case.get('subassembly') for case in similar_cases if case.get('subassembly')})[:5]
            }

            for case in similar_cases[:5]:
                cursor.execute(
                    """
                    INSERT INTO ticket_recommendations (
                        ticket_id, similar_claim_id, similarity_score,
                        recommended_parts, confidence_level, analysis_notes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ticket_id,
                        case.get('claimid'),
                        case.get('similarity_score', 0.0),
                        json.dumps(recommendations),
                        case.get('similarity_score', 0.0),
                        json.dumps(analysis_notes)
                    )
                )
            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
            if self.conn:
                self.conn.rollback()
            return False

        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    # ---------------- Process Ticket ----------------
    def process_existing_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Process an existing ticket by ID"""
        if not self.connect_to_database() or self.conn is None:
            return None

        cursor: Optional[PGCursor] = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                logger.warning(f"Ticket {ticket_id} not found")
                return None

            ticket_dict = dict(ticket)
            cursor.close()
            self.disconnect()

            similar_cases = self.find_similar_issues(ticket_dict['issue_text'], ticket_dict.get('issue_type'), limit=10)
            recommendations: List[Dict[str, Any]] = []
            if similar_cases:
                recommendations = self.extract_recommended_parts(similar_cases)
                self.save_recommendations(ticket_id, similar_cases, recommendations)

            return {
                'ticket_id': ticket_id,
                'ticket_data': ticket_dict,
                'similar_cases': len(similar_cases),
                'recommendations': recommendations,
                'top_similar_cases': [
                    {
                        'claim_id': case['claimid'],
                        'series': case['seriesname'],
                        'subassembly': case['subassembly'],
                        'similarity': round(case.get('similarity_score', 0.0), 3),
                        'symptoms': (case.get('symptomcomments_clean') or '')[:100] + '...',
                        'parts_used': case.get('partname')
                    }
                    for case in similar_cases[:3]
                ]
            }

        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            return None

        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    # ---------------- Get All Tickets ----------------
    def get_all_tickets(self) -> List[Dict[str, Any]]:
        if not self.connect_to_database() or self.conn is None:
            return []

        cursor: Optional[RealDictCursor] = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT t.*, COUNT(tr.id) as recommendation_count
                FROM tickets t
                LEFT JOIN ticket_recommendations tr ON t.ticket_id = tr.ticket_id
                GROUP BY t.ticket_id
                ORDER BY t.created_at DESC
            """)
            tickets = cursor.fetchall()
            return [dict(ticket) for ticket in tickets]

        except Exception as e:
            logger.error(f"Error getting tickets: {e}")
            return []

        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    # ---------------- Get Ticket Recommendations ----------------
    def get_ticket_recommendations(self, ticket_id: int) -> List[Dict[str, Any]]:
        if not self.connect_to_database() or self.conn is None:
            return []

        cursor: Optional[RealDictCursor] = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM ticket_recommendations 
                WHERE ticket_id = %s
                ORDER BY similarity_score DESC
            """, (ticket_id,))
            recs = cursor.fetchall()
            return [dict(rec) for rec in recs]

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

        finally:
            if cursor:
                cursor.close()
            self.disconnect()


# ---------------- Demo Functions ----------------
def process_all_existing_tickets() -> List[Dict[str, Any]]:
    processor = AdaptedTicketProcessor()
    tickets = processor.get_all_tickets()
    results: List[Dict[str, Any]] = []

    if not tickets:
        logger.info("No tickets found in database. Run: python load_tickets.py first")
        return results

    for ticket in tickets:
        if ticket.get('recommendation_count', 0) > 0:
            continue
        result = processor.process_existing_ticket(ticket['ticket_id'])
        if result:
            results.append(result)
    return results


def demo_ticket_analysis() -> None:
    processor = AdaptedTicketProcessor()
    tickets = processor.get_all_tickets()

    if tickets:
        issue_types: Dict[str, List[Dict[str, Any]]] = {}
        for ticket in tickets:
            issue_type = ticket.get('issue_type', 'Unknown')
            issue_types.setdefault(issue_type, []).append(ticket)

        logger.info(f"Tickets by Issue Type: {issue_types.keys()}")
        total_with_recommendations = sum(1 for t in tickets if t.get('recommendation_count', 0) > 0)
        logger.info(f"Tickets with recommendations: {total_with_recommendations}/{len(tickets)}")
    else:
        logger.info("No tickets found")


if __name__ == "__main__":
    results = process_all_existing_tickets()
    demo_ticket_analysis()



# from typing import Optional, Dict, Any, List
# from datetime import datetime
# from psycopg2.extras import RealDictCursor
# from psycopg2.extensions import connection as PGConnection
# import logging
# import json
# from openai import OpenAI
# from ai.db_utils import connect_to_database

# client = OpenAI()

# logger = logging.getLogger(__name__)

# class AdaptedTicketProcessor:
#     def __init__(self):
#         self.conn: Optional[PGConnection] = None

#     def connect_to_database(self) -> bool:
#         """Connect to PostgreSQL database"""
#         self.conn = connect_to_database()  # make sure this returns a psycopg2 connection
#         return self.conn is not None

#     def disconnect(self) -> None:
#         """Close database connection"""
#         if self.conn:
#             self.conn.close()
#             self.conn = None

#     def create_ticket(self, ticket_data: Dict[str, Any]) -> Optional[int]:
#         """Create a new ticket using your schema"""
#         if not self.connect_to_database():
#             return None

#         if self.conn is None:
#             logger.error("Database connection is not established")
#             return None

#         cursor: Optional[RealDictCursor] = None
#         try:
#             cursor = self.conn.cursor(cursor_factory=RealDictCursor)

#             cursor.execute("""
#                 INSERT INTO tickets (
#                     issue_type, issue_text, status, machine_id, user_id, created_at
#                 ) VALUES (
#                     %(issue_type)s, %(issue_text)s, %(status)s, 
#                     %(machine_id)s, %(user_id)s, %(created_at)s
#                 ) RETURNING ticket_id, created_at
#             """, {
#                 'issue_type': ticket_data.get('issue_type'),
#                 'issue_text': ticket_data.get('issue_text'),
#                 'status': ticket_data.get('status', 'open'),
#                 'machine_id': ticket_data.get('machine_id'),
#                 'user_id': ticket_data.get('user_id'),
#                 'created_at': ticket_data.get('created_at', datetime.now())
#             })

#             result = cursor.fetchone()
#             self.conn.commit()

#             if result is None:
#                 logger.error("Ticket creation failed: No ID returned")
#                 return None

#             ticket_id = result['ticket_id']
#             logger.info(f"Ticket created: ID {ticket_id}")
#             return ticket_id

#         except Exception as e:
#             logger.error(f"Error creating ticket: {e}")
#             if self.conn:
#                 self.conn.rollback()
#             return None

#         finally:
#             if cursor:
#                 cursor.close()
#             self.disconnect()

#     # ---------------- Embedding Generator ----------------
#     def generate_openai_embedding(self, text: str) -> List[float]:
#         """Generate embedding using OpenAI (same as used in DB)."""
#         if not text:
#             return [0.0] * 1536  # fallback (OpenAI ada-002 has 1536 dims)

#         response = client.embeddings.create(
#             model="text-embedding-ada-002",  # same model used for DB
#             input=text
#         )
#         return response.data[0].embedding

#     # ------------------------------------------------------

#     def find_similar_issues(self, issue_text, issue_type=None, limit=5, alpha=0.7, min_cutoff=0.65):
#         """
#         Find similar issues using pgvector hybrid search with fallbacks:
#         - First try alpha (symptom weight), retry with adjusted alpha if no results
#         - Use issue_type filter if given, fallback without filter if empty
#         - Larger candidate pool, then top-N returned
#         """
#         if not self.connect_to_database():
#             return []

#         try:
#             cursor = self.conn.cursor(cursor_factory=RealDictCursor)

#             # Generate embedding for query
#             query_embedding = self.generate_openai_embedding(issue_text)
#             if query_embedding is None:
#                 return []

#             def run_query(alpha_value, with_type=True):
#                 fetch_query = """
#                     SELECT 
#                         claimid, seriesname, subseries, subassembly,
#                         symptomcomments, defectcomments, 
#                         symptomcomments_clean, defectcomments_clean,
#                         partname, partquantity,
#                         (
#                             %s * (1 - (embedding_symptom_vector <=> %s::vector)) +
#                             %s * (1 - (embedding_defect_vector <=> %s::vector))
#                         ) AS similarity_score
#                     FROM kubota_parts
#                     WHERE embedding_symptom_vector IS NOT NULL 
#                     AND embedding_defect_vector IS NOT NULL
#                 """

#                 params = [alpha_value, query_embedding, 1 - alpha_value, query_embedding]

#                 if with_type and issue_type:
#                     fetch_query += " AND (seriesname ILIKE %s OR subassembly ILIKE %s)"
#                     params.extend([f"%{issue_type}%", f"%{issue_type}%"])

#                 fetch_query += " ORDER BY similarity_score DESC LIMIT %s"
#                 params.append(20)  # expand candidate pool

#                 cursor.execute(fetch_query, params)
#                 return cursor.fetchall()

#             # --- Try primary search ---
#             rows = run_query(alpha_value=alpha, with_type=True)

#             # --- Fallback: retry with different alpha ---
#             if not rows:
#                 rows = run_query(alpha_value=0.5, with_type=True)

#             # --- Fallback: remove issue_type filter ---
#             if not rows and issue_type:
#                 rows = run_query(alpha_value=alpha, with_type=False)

#             # --- Final Fallback: loosen alpha + no filter ---
#             if not rows:
#                 rows = run_query(alpha_value=0.5, with_type=False)

#             if not rows:
#                 return []

#             # Filter by similarity cutoff
#             filtered = [r for r in rows if r["similarity_score"] >= min_cutoff]

#             # Return top-N after cutoff
#             return filtered[:limit]

#         except Exception as e:
#             print(f"Error finding similar issues: {e}")
#             return []
#         finally:
#             self.disconnect()


#     def extract_recommended_parts(self, similar_cases):
#         """Extract recommended parts from similar cases"""
#         parts_frequency = {}
#         total_cases = len(similar_cases)

#         for case in similar_cases:
#             if case['partname']:
#                 parts = [p.strip() for p in str(case['partname']).split(',')]
#                 for part in parts:
#                     if part and part.lower() != 'nan':
#                         parts_frequency[part] = parts_frequency.get(part, 0) + 1

#         recommendations = []
#         for part, frequency in sorted(parts_frequency.items(), key=lambda x: x[1], reverse=True):
#             confidence = frequency / total_cases
#             recommendations.append({
#                 'part_number': part,
#                 'frequency': frequency,
#                 'confidence': round(confidence, 3),
#                 'recommended_from': f"{frequency}/{total_cases} similar cases"
#             })

#         return recommendations[:10]

#     def save_recommendations(self, ticket_id, similar_cases, recommendations):
#         """Save recommendations to database"""
#         if not self.connect_to_database():
#             return False

#         try:
#             cursor = self.conn.cursor()

#             analysis_notes = {
#                 'total_similar_cases': len(similar_cases),
#                 'avg_similarity': sum(case['similarity_score'] for case in similar_cases) / len(similar_cases) if similar_cases else 0,
#                 'issue_types_found': list(set(case['subassembly'] for case in similar_cases if case['subassembly']))[:5]
#             }

#             for case in similar_cases[:5]:
#                 cursor.execute("""
#                     INSERT INTO ticket_recommendations (
#                         ticket_id, similar_claim_id, similarity_score,
#                         recommended_parts, confidence_level, analysis_notes
#                     ) VALUES (%s, %s, %s, %s, %s, %s)
#                 """, (
#                     ticket_id,
#                     case['claimid'], 
#                     case['similarity_score'],
#                     json.dumps(recommendations),
#                     case['similarity_score'],
#                     json.dumps(analysis_notes)
#                 ))

#             self.conn.commit()
#             cursor.close()
#             return True

#         except Exception as e:
#             print(f"Error saving recommendations: {e}")
#             self.conn.rollback()
#             return False
#         finally:
#             self.disconnect()

#     def process_existing_ticket(self, ticket_id):
#         """Process an existing ticket by ID"""
#         if not self.connect_to_database():
#             return None

#         try:
#             cursor = self.conn.cursor(cursor_factory=RealDictCursor)

#             cursor.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
#             ticket = cursor.fetchone()
#             if not ticket:
#                 print(f"Ticket {ticket_id} not found")
#                 return None

#             cursor.close()
#             self.disconnect()

#             print(f"Processing existing ticket: {ticket_id}")
#             print(f"Type: {ticket['issue_type']}")
#             print(f"Issue: {ticket['issue_text']}")
#             print()

#             print("Searching for similar issues...")
#             similar_cases = self.find_similar_issues(
#                 ticket['issue_text'],
#                 ticket['issue_type'],
#                 limit=10
#             )

#             if similar_cases:
#                 print(f"Found {len(similar_cases)} similar cases")

#                 print("Analyzing parts recommendations...")
#                 recommendations = self.extract_recommended_parts(similar_cases)

#                 if self.save_recommendations(ticket_id, similar_cases, recommendations):
#                     print("Recommendations saved to database")

#                 return {
#                     'ticket_id': ticket_id,
#                     'ticket_data': dict(ticket),
#                     'similar_cases': len(similar_cases),
#                     'recommendations': recommendations,
#                     'top_similar_cases': [
#                         {
#                             'claim_id': case['claimid'],
#                             'series': case['seriesname'],
#                             'subassembly': case['subassembly'],
#                             'similarity': round(case['similarity_score'], 3),
#                             'symptoms': case['symptomcomments_clean'][:100] + '...' if case['symptomcomments_clean'] else '',
#                             'parts_used': case['partname']
#                         }
#                         for case in similar_cases[:3]
#                     ]
#                 }
#             else:
#                 print("No similar cases found")
#                 return {
#                     'ticket_id': ticket_id,
#                     'ticket_data': dict(ticket),
#                     'similar_cases': 0,
#                     'recommendations': [],
#                     'top_similar_cases': []
#                 }

#         except Exception as e:
#             print(f"Error processing ticket: {e}")
#             return None
#         finally:
#             self.disconnect()

#     def get_all_tickets(self):
#         """Get all tickets from database"""
#         if not self.connect_to_database():
#             return []

#         try:
#             cursor = self.conn.cursor(cursor_factory=RealDictCursor)

#             cursor.execute("""
#                 SELECT t.*, COUNT(tr.id) as recommendation_count
#                 FROM tickets t
#                 LEFT JOIN ticket_recommendations tr ON t.ticket_id = tr.ticket_id
#                 GROUP BY t.ticket_id
#                 ORDER BY t.created_at DESC
#             """)

#             tickets = cursor.fetchall()
#             cursor.close()
#             return [dict(ticket) for ticket in tickets]

#         except Exception as e:
#             print(f"Error getting tickets: {e}")
#             return []
#         finally:
#             self.disconnect()

#     def get_ticket_recommendations(self, ticket_id):
#         """Get recommendations for a specific ticket"""
#         if not self.connect_to_database():
#             return []

#         try:
#             cursor = self.conn.cursor(cursor_factory=RealDictCursor)

#             cursor.execute("""
#                 SELECT * FROM ticket_recommendations 
#                 WHERE ticket_id = %s
#                 ORDER BY similarity_score DESC
#             """, (ticket_id,))

#             recommendations = cursor.fetchall()
#             cursor.close()
#             return [dict(rec) for rec in recommendations]

#         except Exception as e:
#             print(f"Error getting recommendations: {e}")
#             return []
#         finally:
#             self.disconnect()


# # Demo functions
# def process_all_existing_tickets():
#     processor = AdaptedTicketProcessor()

#     print("Processing All Existing Tickets")
#     print("=" * 40)

#     tickets = processor.get_all_tickets()
#     if not tickets:
#         print("No tickets found in database")
#         print("Run: python load_tickets.py first")
#         return

#     print(f"Found {len(tickets)} tickets to process")
#     print()

#     results = []

#     for ticket in tickets:
#         print(f"Processing Ticket {ticket['ticket_id']}:")
#         print(f"Type: {ticket['issue_type']}")
#         print(f"Issue: {ticket['issue_text'][:60]}...")
#         print()

#         if ticket['recommendation_count'] > 0:
#             print(f"   Already has {ticket['recommendation_count']} recommendations, skipping")
#             print()
#             continue

#         result = processor.process_existing_ticket(ticket['ticket_id'])

#         if result:
#             results.append(result)
#             print(f"   Found {result['similar_cases']} similar cases")
#             print(f"   Generated {len(result['recommendations'])} parts recommendations")

#             if result['recommendations']:
#                 print("   Top recommendations:")
#                 for i, rec in enumerate(result['recommendations'][:3], 1):
#                     print(f"      {i}. {rec['part_number']} (Confidence: {rec['confidence']:.1%})")
#         else:
#             print("   Processing failed")

#         print("-" * 50)

#     return results

# def demo_ticket_analysis():
#     print("\nDEMO: Ticket Analysis")
#     print("=" * 25)

#     processor = AdaptedTicketProcessor()
#     tickets = processor.get_all_tickets()

#     if tickets:
#         print(f"Total tickets: {len(tickets)}")

#         issue_types = {}
#         for ticket in tickets:
#             issue_type = ticket['issue_type']
#             if issue_type not in issue_types:
#                 issue_types[issue_type] = []
#             issue_types[issue_type].append(ticket)

#         print("\nTickets by Issue Type:")
#         for issue_type, type_tickets in issue_types.items():
#             print(f"   - {issue_type}: {len(type_tickets)} tickets")
#             if type_tickets:
#                 sample = type_tickets[0]
#                 print(f" Example: {sample['issue_text'][:50]}...")

#         total_with_recommendations = sum(1 for ticket in tickets if ticket['recommendation_count'] > 0)
#         print(f"\nTickets with recommendations: {total_with_recommendations}/{len(tickets)}")

#     else:
#         print("No tickets found")


# if __name__ == "__main__":
#     results = process_all_existing_tickets()
#     demo_ticket_analysis()


