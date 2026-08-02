from backend.app.models.rubric import Rubric, RubricRule
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel
from analysis.rubrics.evaluator import rubric_evaluator


def test_rubric_evaluator_scoring():
    rubric = Rubric(
        assignment_id=1,
        title="Test Rubric",
        total_weight=100.0,
        rules=[
            RubricRule(
                rule_code="R_STYLE",
                category="Style",
                weight=30.0,
                penalty_per_violation=5.0,
                max_deduction=15.0,
                is_mandatory=False,
            ),
            RubricRule(
                rule_code="SQL_INJECTION",
                category="Security",
                weight=70.0,
                penalty_per_violation=70.0,
                max_deduction=70.0,
                is_mandatory=True,
            ),
        ],
    )

    static_findings = [
        StaticFindingModel(
            submission_id=1,
            file_path="main.py",
            rule_id="POOR_NAMING",
            category="Style",
            severity="LOW",
            message="Poor name",
            line_start=1,
            line_end=1,
        )
    ]

    sec_findings = [
        SecurityFindingModel(
            submission_id=1,
            file_path="main.py",
            cve_or_rule="SQL_INJECTION",
            vulnerability_type="SQL Injection",
            severity="CRITICAL",
            description="SQLi detected",
            line_number=10,
        )
    ]

    result = rubric_evaluator.evaluate_rubric(
        rubric=rubric,
        max_score=100.0,
        static_findings=static_findings,
        security_findings=sec_findings,
        complexity_metrics=[],
    )

    # Style: 30 - 5 = 25
    # Security: 70 - 70 = 0 (mandatory rule violation)
    # Total earned: 25 / 100 * 100 = 25.0
    assert result.earned_points == 25.0
    assert result.final_score == 25.0
    assert len(result.rule_results) == 2


def test_rubric_evaluation_api_integration(client, test_student, test_instructor):
    # Setup Course & Assignment with Rubric
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS900", "title": "Rubric & Evaluation Systems"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Rubric Lab", "language": "python", "max_score": 100},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Define Rubric
    rubric_res = client.post(
        f"/api/v1/rubrics/assignment/{assign_id}",
        json={
            "title": "Assignment 1 Rubric",
            "rules": [
                {
                    "rule_code": "POOR_NAMING",
                    "category": "Style",
                    "weight": 50.0,
                    "penalty_per_violation": 10.0,
                    "max_deduction": 20.0,
                    "is_mandatory": False,
                },
                {
                    "rule_code": "COMMAND_INJECTION",
                    "category": "Security",
                    "weight": 50.0,
                    "penalty_per_violation": 50.0,
                    "max_deduction": 50.0,
                    "is_mandatory": True,
                },
            ],
        },
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert rubric_res.status_code == 201

    # Student Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "code.py",
                    "content": "def run(x):\n    a = 10\n    return a + x\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Run Analysis (which evaluates Rubric)
    analyze_res = client.post(
        f"/api/v1/submissions/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert analyze_res.status_code == 200
    sub_data = analyze_res.json()
    assert sub_data["score"] is not None

    # Query Rubric Evaluation Breakdown
    eval_res = client.get(
        f"/api/v1/submissions/{sub_id}/rubric-evaluation",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["final_score"] == sub_data["score"]
    assert len(eval_data["rule_results"]) == 2
