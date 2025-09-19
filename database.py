import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database URL
DATABASE_URL: str = os.getenv("DATABASE_URL")  # type: ignore
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=False,  # Set True for SQL query debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Table creation helpers
def create_tables() -> None:
    """Create all tables from models.Base"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def init_db() -> None:
    """Initialize database tables"""
    create_tables()
