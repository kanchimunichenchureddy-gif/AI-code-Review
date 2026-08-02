from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User, RoleEnum
from backend.app.models.assignment import Assignment
from backend.app.models.rubric import Rubric, RubricRule
from backend.app.schemas.rubric import RubricCreate, RubricResponse

router = APIRouter()


@router.post("/assignment/{assignment_id}", response_model=RubricResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_rubric(
    assignment_id: int,
    rubric_in: RubricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN])),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if rubric already exists
    existing_rubric = db.query(Rubric).filter(Rubric.assignment_id == assignment_id).first()
    if existing_rubric:
        db.delete(existing_rubric)
        db.commit()
    
    total_weight = sum(rule.weight for rule in rubric_in.rules)
    rubric = Rubric(
        assignment_id=assignment_id,
        title=rubric_in.title,
        total_weight=total_weight,
    )
    db.add(rubric)
    db.flush()

    for r_rule in rubric_in.rules:
        rule_obj = RubricRule(
            rubric_id=rubric.id,
            rule_code=r_rule.rule_code,
            category=r_rule.category,
            description=r_rule.description,
            weight=r_rule.weight,
            penalty_per_violation=r_rule.penalty_per_violation,
            max_deduction=r_rule.max_deduction,
            is_mandatory=r_rule.is_mandatory,
        )
        db.add(rule_obj)
    
    db.commit()
    db.refresh(rubric)
    return rubric


@router.get("/assignment/{assignment_id}", response_model=RubricResponse)
def get_rubric(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rubric = db.query(Rubric).filter(Rubric.assignment_id == assignment_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not defined for this assignment")
    return rubric
