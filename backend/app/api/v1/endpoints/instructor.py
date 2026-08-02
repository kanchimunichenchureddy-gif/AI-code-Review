from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_role
from backend.app.models.user import User, RoleEnum
from backend.app.models.course import Course
from backend.app.models.submission import Submission
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel, ComplexityMetricModel
from backend.app.models.similarity import SimilarityResultModel
from backend.app.schemas.submission import SubmissionResponse

router = APIRouter()


class ScoreOverrideRequest(BaseModel):
    new_score: float
    reason: str


@router.post("/submissions/{submission_id}/override-score", response_model=SubmissionResponse)
def override_submission_score(
    submission_id: int,
    override_in: ScoreOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA])),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if override_in.new_score < 0 or override_in.new_score > float(submission.assignment.max_score):
        raise HTTPException(
            status_code=400,
            detail=f"Score must be between 0 and assignment max_score ({submission.assignment.max_score})"
        )

    submission.score = override_in.new_score
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/courses/{course_id}/analytics")
def get_course_analytics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA])),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    assignment_ids = [a.id for a in course.assignments]
    submissions = db.query(Submission).filter(Submission.assignment_id.in_(assignment_ids)).all() if assignment_ids else []

    total_submissions = len(submissions)
    scores = [s.score for s in submissions if s.score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    sub_ids = [s.id for s in submissions]

    # Findings metrics
    total_static_findings = db.query(StaticFindingModel).filter(StaticFindingModel.submission_id.in_(sub_ids)).count() if sub_ids else 0
    total_security_findings = db.query(SecurityFindingModel).filter(SecurityFindingModel.submission_id.in_(sub_ids)).count() if sub_ids else 0

    # Plagiarism flags
    plagiarism_flagged_count = (
        db.query(Submission)
        .filter(
            Submission.assignment_id.in_(assignment_ids),
            Submission.plagiarism_similarity_tier.in_(["HIGH", "Requires Human Review"])
        )
        .count()
    ) if assignment_ids else 0

    return {
        "course_id": course.id,
        "course_code": course.code,
        "course_title": course.title,
        "total_enrolled_students": len(course.students),
        "total_assignments": len(course.assignments),
        "total_submissions": total_submissions,
        "class_average_score": avg_score,
        "total_static_findings": total_static_findings,
        "total_security_findings": total_security_findings,
        "plagiarism_flagged_submissions": plagiarism_flagged_count,
    }
