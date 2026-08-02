from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User, RoleEnum
from backend.app.models.course import Course
from backend.app.models.assignment import Assignment
from backend.app.schemas.assignment import AssignmentCreate, AssignmentResponse

router = APIRouter()


@router.get("/course/{course_id}", response_model=List[AssignmentResponse])
def list_assignments_for_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course.assignments


@router.post("/course/{course_id}", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment_for_course(
    course_id: int,
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN])),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    assignment = Assignment(
        title=assignment_in.title,
        description=assignment_in.description,
        course_id=course_id,
        language=assignment_in.language,
        due_date=assignment_in.due_date,
        max_score=assignment_in.max_score,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment
