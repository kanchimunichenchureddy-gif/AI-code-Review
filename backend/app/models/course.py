from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

# Association table for Student Course Enrollment
course_enrollments = Table(
    "course_enrollments",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., CS101
    title = Column(String(255), nullable=False)                         # e.g., Intro to CS
    description = Column(Text, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    instructor = relationship("User", back_populates="created_courses")
    students = relationship("User", secondary=course_enrollments, backref="enrolled_courses")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
