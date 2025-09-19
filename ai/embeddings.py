from .db_utils import connect_to_database
from embedding_utils import parse_embedding_text
from psycopg2.extras import RealDictCursor

def convert_embeddings():
    """Convert existing text embeddings to vector format"""
    print("Converting existing embeddings to vector format")

    conn = connect_to_database()
    if not conn:
        return False

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT claimid, embedding_symptom, embedding_defect 
            FROM kubota_parts 
            WHERE embedding_symptom IS NOT NULL 
               OR embedding_defect IS NOT NULL
            ORDER BY claimid
        """)
        records = cursor.fetchall()
        print(f"Found {len(records)} records with embeddings to convert")

        if len(records) == 0:
            print(" No embedding data found. Check your embedding columns.")
            return False

        success_count = 0

        for i, record in enumerate(records):
            try:
                symptom_vector = None
                if record['embedding_symptom']:
                    symptom_embedding = parse_embedding_text(record['embedding_symptom'])
                    if symptom_embedding:
                        symptom_vector = symptom_embedding

                defect_vector = None
                if record['embedding_defect']:
                    defect_embedding = parse_embedding_text(record['embedding_defect'])
                    if defect_embedding:
                        defect_vector = defect_embedding

                if symptom_vector or defect_vector:
                    cursor.execute("""
                        UPDATE kubota_parts 
                        SET embedding_symptom_vector = %s,
                            embedding_defect_vector = %s
                        WHERE claimid = %s
                    """, (
                        symptom_vector,
                        defect_vector, 
                        record['claimid']
                    ))
                    success_count += 1

                if (i + 1) % 100 == 0 or i == 0:
                    print(f"Processed {i + 1}/{len(records)} records")

            except Exception as e:
                print(f"Error converting record {record['claimid']}: {e}")
                continue

        conn.commit()
        print(f"Successfully converted {success_count}/{len(records)} embeddings!")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f" Conversion failed: {e}")
        conn.rollback()
        return False