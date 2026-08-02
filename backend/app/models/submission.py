import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    score = Column(Float, nullable=True)
    plagiarism_similarity_tier = Column(String(50), default="LOW", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    files = relationship("SubmissionFile", back_populates="submission", cascade="all, delete-orphan")
    findings = relationship("StaticFindingModel", back_populates="submission", cascade="all, delete-orphan")
    security_findings = relationship("SecurityFindingModel", back_populates="submission", cascade="all, delete-orphan")
    complexity_metrics = relationship("ComplexityMetricModel", back_populates="submission", cascade="all, delete-orphan")
    feedback = relationship("FeedbackModel", back_populates="submission", cascade="all, delete-orphan")


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)

    # Relationships
    submission = relationship("Submission", back_populates="files")
