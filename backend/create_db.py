#!/usr/bin/env python3
"""
Create database tables with proper schema
"""

from app.db.session import engine, Base
from app.models.email_scan import EmailScan

def create_database():
    """Create all database tables."""
    print("🗄️ Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print(f"📊 Tables: {list(Base.metadata.tables.keys())}")
    
    # Show EmailScan table structure
    email_scan_table = Base.metadata.tables['email_scans']
    print(f"📋 EmailScan columns: {[col.name for col in email_scan_table.columns]}")

if __name__ == "__main__":
    create_database()