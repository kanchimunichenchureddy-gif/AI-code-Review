from typing import List
from pydantic import BaseModel, ConfigDict


class RuleEvaluationResponse(BaseModel):
    rule_code: str
    category: str
    weight: float
    violations_count: int
    deduction: float
    score: float
    is_mandatory: bool
    passed: bool
    details: str

    model_config = ConfigDict(from_attributes=True)


class RubricEvaluationResponse(BaseModel):
    total_weight: float
    earned_points: float
    final_score: float
    rule_results: List[RuleEvaluationResponse]

    model_config = ConfigDict(from_attributes=True)
