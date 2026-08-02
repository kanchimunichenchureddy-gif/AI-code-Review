from dataclasses import dataclass
from typing import List, Dict, Any
from backend.app.models.rubric import Rubric, RubricRule
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel, ComplexityMetricModel


@dataclass
class RuleEvaluationResult:
    rule_code: str
    category: str
    weight: float
    violations_count: int
    deduction: float
    score: float
    is_mandatory: bool
    passed: bool
    details: str


@dataclass
class RubricEvaluationResult:
    total_weight: float
    earned_points: float
    final_score: float
    rule_results: List[RuleEvaluationResult]


class RubricEvaluator:
    def evaluate_rubric(
        self,
        rubric: Rubric,
        max_score: float,
        static_findings: List[StaticFindingModel],
        security_findings: List[SecurityFindingModel],
        complexity_metrics: List[ComplexityMetricModel],
    ) -> RubricEvaluationResult:

        rule_results: List[RuleEvaluationResult] = []
        total_earned_weight = 0.0
        total_possible_weight = rubric.total_weight if rubric.total_weight > 0 else 100.0

        for rule in rubric.rules:
            violations_count = 0
            details_list = []

            # 1. Check Security findings matching category or rule_code
            if rule.category.upper() == "SECURITY" or "SEC" in rule.rule_code.upper():
                sec_matches = [
                    f for f in security_findings
                    if rule.rule_code in f.cve_or_rule or rule.category.upper() == "SECURITY"
                ]
                violations_count += len(sec_matches)
                if sec_matches:
                    details_list.append(f"{len(sec_matches)} security issue(s) detected.")

            # 2. Check Static findings matching rule_code or category
            cat_static_matches = [
                f for f in static_findings
                if f.rule_id == rule.rule_code or f.category.upper() == rule.category.upper()
            ]
            violations_count += len(cat_static_matches)
            if cat_static_matches:
                details_list.append(f"{len(cat_static_matches)} '{rule.category}' code smell(s) detected.")

            # 3. Check Complexity metrics matching rule_code thresholds
            if "COMPLEXITY" in rule.rule_code.upper() or rule.category.upper() == "COMPLEXITY":
                high_comp = [m for m in complexity_metrics if m.cyclomatic_complexity > 10]
                if high_comp:
                    violations_count += len(high_comp)
                    details_list.append(f"{len(high_comp)} function(s) exceed cyclomatic complexity threshold (>10).")

            # Compute deductions
            deduction = min(rule.max_deduction, violations_count * rule.penalty_per_violation)
            if rule.is_mandatory and violations_count > 0:
                deduction = rule.max_deduction

            earned_score = max(0.0, rule.weight - deduction)
            total_earned_weight += earned_score
            passed = violations_count == 0

            details = "; ".join(details_list) if details_list else "All constraints satisfied."

            rule_results.append(
                RuleEvaluationResult(
                    rule_code=rule.rule_code,
                    category=rule.category,
                    weight=rule.weight,
                    violations_count=violations_count,
                    deduction=round(deduction, 2),
                    score=round(earned_score, 2),
                    is_mandatory=rule.is_mandatory,
                    passed=passed,
                    details=details,
                )
            )

        # Final score calculation normalized to assignment max_score
        score_percentage = total_earned_weight / total_possible_weight if total_possible_weight > 0 else 1.0
        final_score = max(0.0, min(max_score, score_percentage * max_score))

        return RubricEvaluationResult(
            total_weight=total_possible_weight,
            earned_points=round(total_earned_weight, 2),
            final_score=round(final_score, 2),
            rule_results=rule_results,
        )


rubric_evaluator = RubricEvaluator()
