from .db_utils import connect_to_database

def create_vector_indexes():
    """Create vector indexes for similarity search"""
    print("\n Creating vector indexes...")

    conn = connect_to_database()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        indexes = [
            ("idx_symptom_vector", "embedding_symptom_vector"),
            ("idx_defect_vector", "embedding_defect_vector")
        ]

        for index_name, column_name in indexes:
            try:
                print(f"   Creating index {index_name}...")
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON kubota_parts 
                    USING hnsw ({column_name} vector_cosine_ops)
                """)
                print(f"   Index {index_name} created")
            except Exception as e:
                print(f"   Index {index_name} creation: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print(" Vector indexes created successfully!")
        return True

    except Exception as e:
        print(f"Index creation failed: {e}")
        return False