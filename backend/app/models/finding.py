import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    fingerprint = Column(String(16), nullable=False, index=True)
    vulnerability_type = Column(String(100), nullable=False)
    cwe_id = Column(String(20), nullable=True)
    severity = Column(String(20), nullable=False)
    confidence = Column(String(20), nullable=False, default="medium")
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    code_snippet = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    attack_scenario = Column(Text, nullable=False)
    remediation = Column(Text, nullable=False)
    status = Column(String(20), default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="findings")
