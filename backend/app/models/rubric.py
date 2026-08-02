from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    total_weight = Column(Float, default=100.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment = relationship("Assignment", back_populates="rubric")
    rules = relationship("RubricRule", back_populates="rubric", cascade="all, delete-orphan")


class RubricRule(Base):
    __tablename__ = "rubric_rules"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False)
    rule_code = Column(String(100), nullable=False)  # e.g., R_COMPLEXITY_INSERT
    category = Column(String(100), nullable=False)   # Style, Complexity, Security, Performance, Correctness
    description = Column(Text, nullable=True)
    weight = Column(Float, default=10.0, nullable=False)
    penalty_per_violation = Column(Float, default=2.0, nullable=False)
    max_deduction = Column(Float, default=10.0, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)

    # Relationships
    rubric = relationship("Rubric", back_populates="rules")
