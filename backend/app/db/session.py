"""
Database session management and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import Generator

from app.core.config import settings


# Create declarative base
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    # Import all models to ensure they are registered with Base
    from app.models.email_scan import EmailScan
    from app.models.voice_scan import VoiceScan
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
