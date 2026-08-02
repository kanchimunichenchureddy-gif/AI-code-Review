from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.core import security
from backend.app.core.config import settings
from backend.app.models.user import User, RoleEnum
from backend.app.models.course import Course
from backend.app.models.assignment import Assignment
from backend.app.models.rubric import Rubric, RubricRule
from backend.app.models.submission import Submission, SubmissionFile, SubmissionStatus
from backend.app.schemas.token import Token
from backend.app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user_email = db.query(User).filter(User.email == user_in.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )
    db_user_uname = db.query(User).filter(User.username == user_in.username).first()
    if db_user_uname:
        raise HTTPException(
            status_code=400, detail="Username already taken"
        )
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    # Support login by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.username, expires_delta=access_token_expires, role=user.role.value
        ),
        "token_type": "bearer",
    }


@router.post("/demo-login", response_model=Token)
def demo_login_shortcut(role: str = "student", db: Session = Depends(get_db)):
    target_role = RoleEnum.STUDENT if role.lower() == "student" else RoleEnum.INSTRUCTOR
    username = f"demo_{target_role.value}"
    email = f"{username}@university.edu"
    full_name = f"Demo {target_role.value.capitalize()}"
    password = "demopassword123"

    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=security.get_password_hash(password),
            role=target_role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Reset password to ensure demopassword123 works
        user.hashed_password = security.get_password_hash(password)
        db.commit()

    # Ensure demo_instructor user exists for course creation
    inst_user = db.query(User).filter(User.role == RoleEnum.INSTRUCTOR).first()
    if not inst_user:
        inst_user = User(
            email="demo_instructor@university.edu",
            username="demo_instructor",
            full_name="Prof Demo Instructor",
            hashed_password=security.get_password_hash(password),
            role=RoleEnum.INSTRUCTOR,
            is_active=True,
        )
        db.add(inst_user)
        db.commit()
        db.refresh(inst_user)

    # Seed Course & Assignment & Submission if empty
    course = db.query(Course).first()
    if not course:
        course = Course(
            code="CS101",
            title="Introduction to Computer Science",
            description="Demo Course",
            instructor_id=inst_user.id,
        )
        db.add(course)
        db.commit()
        db.refresh(course)

    assign = db.query(Assignment).first()
    if not assign:
        assign = Assignment(course_id=course.id, title="Python Basics", language="python", max_score=100)
        db.add(assign)
        db.commit()
        db.refresh(assign)

        rubric = Rubric(assignment_id=assign.id, title="CS101 Rubric", total_weight=100.0)
        db.add(rubric)
        db.flush()

        r1 = RubricRule(rubric_id=rubric.id, rule_code="POOR_NAMING", category="Style", weight=30.0, penalty_per_violation=5.0, max_deduction=15.0)
        r2 = RubricRule(rubric_id=rubric.id, rule_code="SQL_INJECTION", category="Security", weight=70.0, penalty_per_violation=70.0, max_deduction=70.0, is_mandatory=True)
        db.add_all([r1, r2])
        db.commit()

    sub = db.query(Submission).first()
    if not sub:
        sub = Submission(assignment_id=assign.id, student_id=user.id, status=SubmissionStatus.COMPLETED, attempt_number=1, score=90.0)
        db.add(sub)
        db.flush()

        sf = SubmissionFile(submission_id=sub.id, filename="main.py", content="def calculate_sum(data):\n    s = 0\n    for item in data:\n        s += item\n    return s\n", language="python")
        db.add(sf)
        db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.username, expires_delta=access_token_expires, role=user.role.value
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    return current_user
