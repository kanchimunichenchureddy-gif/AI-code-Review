from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User, RoleEnum
from backend.app.models.course import Course, course_enrollments
from backend.app.schemas.course import CourseCreate, CourseResponse, EnrollmentAdd

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN]:
        return db.query(Course).all()
    # For students/TAs, return enrolled courses + open courses
    return current_user.enrolled_courses


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN])),
):
    existing = db.query(Course).filter(Course.code == course_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course code already exists")
    
    course = Course(
        code=course_in.code,
        title=course_in.title,
        description=course_in.description,
        instructor_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/{course_id}/enroll", response_model=CourseResponse)
def enroll_student_in_course(
    course_id: int,
    enroll_in: EnrollmentAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA])),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    student = db.query(User).filter(User.email == enroll_in.user_email).first()
    if not student:
        raise HTTPException(status_code=404, detail="User with provided email not found")

    if student not in course.students:
        course.students.append(student)
        db.commit()
        db.refresh(course)
    return course
