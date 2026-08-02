from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.models.submission import SubmissionStatus


class SubmissionFileCreate(BaseModel):
    filename: str
    content: str
    language: str = "python"


class SubmissionFileResponse(SubmissionFileCreate):
    id: int
    submission_id: int

    model_config = ConfigDict(from_attributes=True)


class StaticFindingResponse(BaseModel):
    id: int
    file_path: str
    rule_id: str
    category: str
    severity: str
    message: str
    line_start: int
    line_end: int
    col_start: Optional[int] = None
    col_end: Optional[int] = None
    evidence_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityFindingResponse(BaseModel):
    id: int
    file_path: str
    cve_or_rule: str
    vulnerability_type: str
    severity: str
    description: str
    line_number: int
    evidence_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ComplexityMetricResponse(BaseModel):
    id: int
    file_path: str
    function_name: Optional[str] = None
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    lines_of_code: int
    nesting_depth: int

    model_config = ConfigDict(from_attributes=True)


class FeedbackResponse(BaseModel):
    id: int
    category: str
    title: str
    what_text: str
    why_text: str
    how_to_fix_text: str
    example_code: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionCreate(BaseModel):
    files: List[SubmissionFileCreate]


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    status: SubmissionStatus
    score: Optional[float] = None
    plagiarism_similarity_tier: str
    created_at: datetime
    files: List[SubmissionFileResponse] = []
    findings: List[StaticFindingResponse] = []
    security_findings: List[SecurityFindingResponse] = []
    complexity_metrics: List[ComplexityMetricResponse] = []
    feedback: List[FeedbackResponse] = []

    model_config = ConfigDict(from_attributes=True)
