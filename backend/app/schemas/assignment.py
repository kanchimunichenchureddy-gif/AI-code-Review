from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.rubric import RubricResponse


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    language: str = "python"
    due_date: Optional[datetime] = None
    max_score: int = 100


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentResponse(AssignmentBase):
    id: int
    course_id: int
    is_active: bool
    created_at: datetime
    rubric: Optional[RubricResponse] = None

    model_config = ConfigDict(from_attributes=True)
