from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User, RoleEnum
from backend.app.models.course import Course
from backend.app.models.submission import Submission
from reports.export_service import report_export_service

router = APIRouter()


@router.get("/course/{course_id}/gradebook")
def export_course_gradebook_csv(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA])),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    csv_data = report_export_service.generate_csv_gradebook(db, course_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={course.code}_gradebook.csv"
        },
    )


@router.get("/submission/{submission_id}/export")
def export_submission_report_json(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to export this report")

    report_json = report_export_service.generate_submission_report_json(db, submission)
    return report_json
