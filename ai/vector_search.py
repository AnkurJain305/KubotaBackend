from .db_utils import connect_to_database
from psycopg2.extras import RealDictCursor

def test_vector_search():
    """Test vector similarity search"""
    print("\n Testing vector similarity search...")

    conn = connect_to_database()
    if not conn:
        return False

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT claim_id, series_name, sub_assembly, 
                   symptom_comments_clean, embedding_symptom
            FROM kubota_parts 
            WHERE embedding_symptom IS NOT NULL 
            LIMIT 1
        """)
        sample = cursor.fetchone()
        if not sample:
            print(" No vector data found for testing")
            return False

        print(f" Using sample record: {sample['claim_id']}")
        print(f"   Series: {sample['series_name']}")
        print(f"   Issue: {sample['symptom_comments_clean'][:100]}...")

        cursor.execute("""
            SELECT claim_id, series_name, sub_assembly,
                   symptom_comments_clean,
                   1 - (embedding_symptom <=> %s) as similarity_score
            FROM kubota_parts 
            WHERE embedding_symptom IS NOT NULL
              AND claim_id != %s
            ORDER BY embedding_symptom <=> %s
            LIMIT 3
        """, (sample['embedding_symptom'], sample['claim_id'], sample['embedding_symptom']))

        similar_records = cursor.fetchall()

        if similar_records:
            print(f"\nFound {len(similar_records)} similar records:")
            for i, record in enumerate(similar_records, 1):
                print(f"\n   {i}. Claim: {record['claim_id']}")
                print(f"      Series: {record['series_name']} - {record['sub_assembly']}")
                print(f"      Similarity: {record['similarity_score']:.3f}")
                print(f"      Issue: {record['symptom_comments_clean'][:100]}...")
        else:
            print("No similar records found")
            return False

        cursor.close()
        conn.close()

        print("\nVector similarity search is working!")
        return True

    except Exception as e:
        print(f" Vector search test failed: {e}")
        return False

def check_vector_data(): 
    """Check vector conversion results"""
    print("\nChecking vector conversion results...")

    conn = connect_to_database()
    if not conn:
        return

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Stats about vectors
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(embedding_symptom) as symptom_vectors,
                COUNT(embedding_defect) as defect_vectors,
                COUNT(CASE WHEN embedding_symptom IS NOT NULL 
                           OR embedding_defect IS NOT NULL THEN 1 END) as records_with_vectors
            FROM kubota_parts
        """)
        stats = cursor.fetchone()  
        # print(f"   Total records: {stats['total_records']}")
        # print(f"   Records with symptom vectors: {stats['symptom_vectors']}")
        # print(f"   Records with defect vectors: {stats['defect_vectors']}")
        # print(f"   Records with any vectors: {stats['records_with_vectors']}")

        # Check dimensions using cardinality() for vector type
        cursor.execute("""
            SELECT embedding_symptom
            FROM kubota_parts
            WHERE embedding_symptom IS NOT NULL
            LIMIT 1
        """)
        dim_result = cursor.fetchone()
        if dim_result and dim_result['embedding_symptom']:
            print(f"   Vector dimensions: {len(dim_result['embedding_symptom'])}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error checking vector data: {e}")
