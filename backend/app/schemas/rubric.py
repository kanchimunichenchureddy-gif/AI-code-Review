from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RubricRuleBase(BaseModel):
    rule_code: str
    category: str
    description: Optional[str] = None
    weight: float = 10.0
    penalty_per_violation: float = 2.0
    max_deduction: float = 10.0
    is_mandatory: bool = False


class RubricRuleCreate(RubricRuleBase):
    pass


class RubricRuleResponse(RubricRuleBase):
    id: int
    rubric_id: int

    model_config = ConfigDict(from_attributes=True)


class RubricCreate(BaseModel):
    title: str
    rules: List[RubricRuleCreate] = []


class RubricResponse(BaseModel):
    id: int
    assignment_id: int
    title: str
    total_weight: float
    rules: List[RubricRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)
