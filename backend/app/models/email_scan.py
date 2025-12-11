# backend/app/models/email_scan.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.session import Base

class EmailScan(Base):
    __tablename__ = "email_scans"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(512), nullable=True)
    sender = Column(String(256), nullable=True)
    label = Column(String(32), nullable=True)
    score = Column(Integer, nullable=True)
    reasons = Column(Text, nullable=True)
    analysis_meta = Column(Text, nullable=True)  # JSON text if needed
    created_at = Column(DateTime, default=datetime.utcnow)
