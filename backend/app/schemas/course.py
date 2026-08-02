from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.user import UserResponse


class CourseBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    created_at: datetime
    instructor: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentAdd(BaseModel):
    user_email: str
