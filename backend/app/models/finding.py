from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class StaticFindingModel(Base):
    __tablename__ = "static_findings"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    rule_id = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    col_start = Column(Integer, nullable=True)
    col_end = Column(Integer, nullable=True)
    evidence_snippet = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="findings")


class SecurityFindingModel(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    cve_or_rule = Column(String(100), nullable=False)  # SQLi, Command Injection, etc.
    vulnerability_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=False)
    evidence_snippet = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="security_findings")


class ComplexityMetricModel(Base):
    __tablename__ = "complexity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    function_name = Column(String(255), nullable=True)
    cyclomatic_complexity = Column(Integer, nullable=False)
    cognitive_complexity = Column(Integer, nullable=False)
    maintainability_index = Column(Float, nullable=False)
    lines_of_code = Column(Integer, nullable=False)
    nesting_depth = Column(Integer, nullable=False)

    submission = relationship("Submission", back_populates="complexity_metrics")


class FeedbackModel(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    what_text = Column(Text, nullable=False)
    why_text = Column(Text, nullable=False)
    how_to_fix_text = Column(Text, nullable=False)
    example_code = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    submission = relationship("Submission", back_populates="feedback")
