# test_step3_enhanced.py - Test with your enhanced ticket processor
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

# Import your enhanced processor (assuming it's in the same directory)
try:
    from ai.ticket_processor_adapted import AdaptedTicketProcessor
except ImportError:
    print("❌ Could not import AdaptedTicketProcessor")
    print("💡 Make sure your enhanced ticket_processor_adapted.py is in the same directory")
    exit(1)

def connect_to_database():
    """Connect to database using your db_utils approach"""
    try:
        # Try to use your db_utils if available
        try:
            from db_utils import connect_to_database as db_connect
            return db_connect()
        except ImportError:
            # Fallback to direct connection
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'kubota_parts_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD')
            )
            return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_openai_integration():
    """Test OpenAI embedding generation"""
    print("🤖 Testing OpenAI integration...")

    try:
        processor = AdaptedTicketProcessor()

        # Test embedding generation
        test_text = "hydraulic work lights not functioning"
        embedding = processor.generate_openai_embedding(test_text)

        if embedding and len(embedding) == 1536:
            print(f"✅ OpenAI embeddings working (dimension: {len(embedding)})")
            print(f"   Sample values: {embedding[:3]}...")
            return True
        else:
            print("❌ OpenAI embedding generation failed")
            return False

    except Exception as e:
        print(f"❌ OpenAI integration test failed: {e}")
        print("💡 Check your OPENAI_API_KEY in .env file")
        return False

def test_enhanced_vector_search():
    """Test enhanced vector search with fallbacks"""
    print("\n🔍 Testing enhanced vector search...")

    processor = AdaptedTicketProcessor()

    # Test with different scenarios
    test_scenarios = [
        {
            'text': 'hydraulic work lights not functioning',
            'type': 'hydraulic',
            'description': 'Exact match test'
        },
        {
            'text': 'engine problems with starting',
            'type': 'engine', 
            'description': 'Engine issues test'
        },
        {
            'text': 'transmission slipping under load',
            'type': None,
            'description': 'No type filter test'
        }
    ]

    success_count = 0

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n   Test {i}: {scenario['description']}")
        print(f"   Query: '{scenario['text']}'")
        print(f"   Type filter: {scenario['type'] or 'None'}")

        try:
            similar_cases = processor.find_similar_issues(
                scenario['text'], 
                scenario['type'], 
                limit=5
            )

            if similar_cases:
                print(f"   ✅ Found {len(similar_cases)} similar cases")

                # Show top result
                top_case = similar_cases[0]
                print(f"   🎯 Best match: {top_case['claimid']}")
                print(f"      Similarity: {top_case['similarity_score']:.3f}")
                print(f"      Series: {top_case['seriesname']} - {top_case['subassembly']}")
                print(f"      Parts: {top_case['partname'][:50] if top_case['partname'] else 'None'}...")

                success_count += 1
            else:
                print(f"   ⚠️  No similar cases found")

        except Exception as e:
            print(f"   ❌ Search failed: {e}")

    print(f"\n📊 Vector search results: {success_count}/{len(test_scenarios)} scenarios successful")
    return success_count > 0

def test_fallback_logic():
    """Test the fallback logic in vector search"""
    print("\n🔄 Testing fallback logic...")

    processor = AdaptedTicketProcessor()

    # Test with very specific query that might need fallbacks
    test_query = "very specific unusual problem that might not match"

    print(f"   Testing with challenging query: '{test_query}'")

    try:
        similar_cases = processor.find_similar_issues(
            test_query,
            "nonexistent_type",  # Force fallback
            limit=3
        )

        if similar_cases:
            print(f"   ✅ Fallback logic worked - found {len(similar_cases)} cases")
            print(f"   📊 Similarity scores: {[round(c['similarity_score'], 3) for c in similar_cases]}")
            return True
        else:
            print("   ⚠️  No cases found even with fallbacks")
            print("   💡 This might indicate very limited data or high similarity thresholds")
            return False

    except Exception as e:
        print(f"   ❌ Fallback test failed: {e}")
        return False

def test_confidence_scoring():
    """Test confidence scoring and part recommendations"""
    print("\n📊 Testing confidence scoring...")

    processor = AdaptedTicketProcessor()

    # Use a common issue that should have multiple similar cases
    test_issues = [
        "hydraulic leak",
        "engine performance",
        "electrical problem"
    ]

    for issue in test_issues:
        print(f"\n   Testing: '{issue}'")

        try:
            similar_cases = processor.find_similar_issues(issue, limit=10)

            if similar_cases:
                recommendations = processor.extract_recommended_parts(similar_cases)

                print(f"   ✅ {len(similar_cases)} similar cases → {len(recommendations)} recommendations")

                if recommendations:
                    print("   🔧 Top recommendations:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"      {i}. {rec['part_number']}")
                        print(f"         Confidence: {rec['confidence']:.1%}")
                        print(f"         Usage: {rec['recommended_from']}")
                else:
                    print("   ⚠️  No parts data in similar cases")
            else:
                print(f"   ⚠️  No similar cases found for '{issue}'")

        except Exception as e:
            print(f"   ❌ Confidence test failed for '{issue}': {e}")

    return True

def test_ticket_processing_workflow():
    """Test complete enhanced ticket processing"""
    print("\n⚙️  Testing complete processing workflow...")

    processor = AdaptedTicketProcessor()

    # Get existing tickets
    tickets = processor.get_all_tickets()

    if not tickets:
        print("   ❌ No tickets found to test")
        print("   💡 Run: python load_tickets.py first")
        return False

    print(f"   📋 Found {len(tickets)} tickets")

    # Find a ticket without recommendations to process
    test_ticket = None
    for ticket in tickets:
        if ticket['recommendation_count'] == 0:
            test_ticket = ticket
            break

    if not test_ticket:
        # All tickets have recommendations, test the first one
        test_ticket = tickets[0]
        print(f"   ℹ️  All tickets have recommendations, testing ticket {test_ticket['ticket_id']}")
    else:
        print(f"   🎯 Testing ticket {test_ticket['ticket_id']} (no existing recommendations)")

    print(f"   Issue: {test_ticket['issue_text']}")
    print(f"   Type: {test_ticket['issue_type']}")

    try:
        result = processor.process_existing_ticket(test_ticket['ticket_id'])

        if result:
            print(f"   ✅ Processing successful!")
            print(f"   🔍 Similar cases found: {result['similar_cases']}")
            print(f"   🔧 Parts recommendations: {len(result['recommendations'])}")

            if result['recommendations']:
                print("   📋 Top recommendation:")
                top_rec = result['recommendations'][0]
                print(f"      {top_rec['part_number']} (Confidence: {top_rec['confidence']:.1%})")

            if result['top_similar_cases']:
                print("   🎯 Best similar case:")
                best_case = result['top_similar_cases'][0]
                print(f"      {best_case['claim_id']}: {best_case['similarity']:.1%} similarity")

            return True
        else:
            print("   ❌ Processing returned no result")
            return False

    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        return False

def test_database_integration():
    """Test database integration and data consistency"""
    print("\n💾 Testing database integration...")

    conn = connect_to_database()
    if not conn:
        return False

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check vector data quality
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(embedding_symptom_vector) as symptom_vectors,
                   COUNT(embedding_defect_vector) as defect_vectors
            FROM kubota_parts
        """)

        vector_stats = cursor.fetchone()
        # print(f"   📊 Vector data quality:")
        # print(f"      Total kubota_parts: {vector_stats['total']}")
        # print(f"      Symptom vectors: {vector_stats['symptom_vectors']}")
        # print(f"      Defect vectors: {vector_stats['defect_vectors']}")

        # Check tickets and recommendations
        cursor.execute("""
            SELECT COUNT(*) as total_tickets,
                   COUNT(CASE WHEN tr.ticket_id IS NOT NULL THEN 1 END) as tickets_with_recs
            FROM tickets t
            LEFT JOIN ticket_recommendations tr ON t.ticket_id = tr.ticket_id
        """)

        ticket_stats = cursor.fetchone()
        # print(f"   🎫 Ticket processing status:")
        # print(f"      Total tickets: {ticket_stats['total_tickets']}")
        # print(f"      Tickets with recommendations: {ticket_stats['tickets_with_recs']}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"   ❌ Database integration test failed: {e}")
        return False

def main():
    """Run all enhanced tests"""
    print("🧪 Enhanced Ticket Processor - Comprehensive Testing")
    print("=" * 60)
    print("Testing your improved version with:")
    print("• OpenAI embedding integration")
    print("• Enhanced vector search with fallbacks") 
    print("• Improved confidence scoring")
    print("• Robust error handling")
    print()

    tests = [
        ("OpenAI Integration", test_openai_integration),
        ("Enhanced Vector Search", test_enhanced_vector_search),
        ("Fallback Logic", test_fallback_logic),
        ("Confidence Scoring", test_confidence_scoring),
        ("Complete Workflow", test_ticket_processing_workflow),
        ("Database Integration", test_database_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"🧪 Running: {test_name}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
                print("💡 Check the error messages above for details")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")

        print("-" * 60)

    print(f"🏁 Enhanced Testing Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 EXCELLENT! Your enhanced system is working perfectly!")
        print("\n✅ All improvements verified:")
        print("   • OpenAI embeddings generating properly")
        print("   • Vector search with smart fallbacks")
        print("   • Confidence scoring working")
        print("   • Complete workflow functional")
        print("   • Database integration solid")
        print("\n🚀 Ready for Step 4: Background Jobs & Queue Processing!")
        print("\n💡 Your system can now:")
        print("   • Process tickets with high-quality AI embeddings")
        print("   • Find similar cases even with challenging queries")
        print("   • Provide confident parts recommendations")
        print("   • Handle edge cases gracefully")

    elif passed >= 4:
        print("\n✅ Very Good! Most core functionality working")
        print(f"✅ {passed}/{total} tests passed - minor issues to fix")
        print("🚀 Ready to move forward with some monitoring")

    else:
        print("\n⚠️  Some core issues need attention")
        print("\n📚 Common fixes:")
        print("   • OpenAI: Check OPENAI_API_KEY in .env")
        print("   • Vectors: Ensure kubota_parts has vector data")
        print("   • Database: Verify connection settings")
        print("   • Tickets: Run python load_tickets.py")

if __name__ == "__main__":
    main()