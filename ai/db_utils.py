import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'kubota_backend'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASS', 'admin')
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None