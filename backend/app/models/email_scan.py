# app/models/email_scan.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.session import Base

class EmailScan(Base):
    __tablename__ = "email_scans"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(512), nullable=True)
    sender = Column(String(256), nullable=True)
    label = Column(String(32), nullable=True)
    score = Column(Integer, nullable=True)
    reasons = Column(Text, nullable=True)
    analysis_metadata = Column(Text, nullable=True)  # Store analysis metadata (AI usage, cost, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
