# oracle/app/database.py
"""
Database connection and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(dotenv_path="../../.env")

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Admin123@localhost:5432/msme_finance"
)

print(f"Database URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[-1], '****')}")  # Hide password in logs

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI routes to get database session
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session in scripts
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database (create all tables)
    """
    # Import models here to avoid circular imports
    try:
        from models import Base  # Changed from 'app.models' to just 'models'
    except ImportError:
        # If running from parent directory
        from app.models import Base
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_db():
    """
    Drop all database tables (DANGEROUS - use only in development)
    """
    try:
        from models import Base
    except ImportError:
        from app.models import Base
    
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")