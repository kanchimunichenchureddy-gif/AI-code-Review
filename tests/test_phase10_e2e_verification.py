import pytest
from backend.app.models.user import User, RoleEnum
from backend.app.core.security import get_password_hash


def test_system_health_check(client):
    res = client.get("/api/v1/health/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "python" in data["supported_languages"]


def test_full_academic_term_end_to_end_lifecycle(client, db_session):
    # 1. Instructor Registration & Login
    inst = User(
        email="prof_e2e@university.edu",
        username="prof_e2e",
        full_name="Prof E2E",
        hashed_password=get_password_hash("e2epass123"),
        role=RoleEnum.INSTRUCTOR,
        is_active=True,
    )
    db_session.add(inst)

    # 2. Student 1 & Student 2 Registration
    std1 = User(
        email="student1_e2e@university.edu",
        username="student1_e2e",
        full_name="Student One",
        hashed_password=get_password_hash("studentpass123"),
        role=RoleEnum.STUDENT,
        is_active=True,
    )
    std2 = User(
        email="student2_e2e@university.edu",
        username="student2_e2e",
        full_name="Student Two",
        hashed_password=get_password_hash("studentpass123"),
        role=RoleEnum.STUDENT,
        is_active=True,
    )
    db_session.add_all([std1, std2])
    db_session.commit()

    # Instructor Login
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_e2e", "password": "e2epass123"})
    assert inst_login.status_code == 200
    inst_token = inst_login.json()["access_token"]

    # 3. Create Course & Assignment with Rubric
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS-E2E", "title": "End to End Master Course"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "E2E Capstone Project", "language": "python", "max_score": 100},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert assign_res.status_code == 201
    assign_id = assign_res.json()["id"]

    rubric_res = client.post(
        f"/api/v1/rubrics/assignment/{assign_id}",
        json={
            "title": "E2E Grading Rubric",
            "rules": [
                {
                    "rule_code": "SQL_INJECTION",
                    "category": "Security",
                    "weight": 50.0,
                    "penalty_per_violation": 50.0,
                    "max_deduction": 50.0,
                    "is_mandatory": True,
                },
                {
                    "rule_code": "POOR_NAMING",
                    "category": "Style",
                    "weight": 50.0,
                    "penalty_per_violation": 10.0,
                    "max_deduction": 20.0,
                    "is_mandatory": False,
                },
            ],
        },
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert rubric_res.status_code == 201

    # 4. Student 1 Submits Code
    std1_login = client.post("/api/v1/auth/login", data={"username": "student1_e2e", "password": "studentpass123"})
    std1_token = std1_login.json()["access_token"]

    sub1_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "solution.py",
                    "content": "def calculate_discount(price_amount):\n    val_acc = price_amount * 0.1\n    return val_acc\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std1_token}"},
    )
    assert sub1_res.status_code == 201
    sub1_id = sub1_res.json()["id"]

    # 5. Student 2 Submits Similar Code (Renamed variables to test plagiarism)
    std2_login = client.post("/api/v1/auth/login", data={"username": "student2_e2e", "password": "studentpass123"})
    std2_token = std2_login.json()["access_token"]

    sub2_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "solution.py",
                    "content": "def calculate_discount(orig_cost):\n    total_res = orig_cost * 0.1\n    return total_res\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std2_token}"},
    )
    assert sub2_res.status_code == 201
    sub2_id = sub2_res.json()["id"]

    # 6. Run Full Analysis on Submissions
    client.post(f"/api/v1/submissions/{sub1_id}/analyze", headers={"Authorization": f"Bearer {std1_token}"})
    client.post(f"/api/v1/submissions/{sub2_id}/analyze", headers={"Authorization": f"Bearer {std2_token}"})

    # 7. Run Plagiarism Check
    plag_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}/check-plagiarism",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert plag_res.status_code == 200
    assert len(plag_res.json()) >= 2

    # 8. Generate Evidence-Bound AI Educational Feedback
    fb_res = client.post(
        f"/api/v1/submissions/{sub1_id}/generate-feedback",
        headers={"Authorization": f"Bearer {std1_token}"},
    )
    assert fb_res.status_code == 200

    # 9. Instructor Manual Score Override
    override_res = client.post(
        f"/api/v1/instructor/submissions/{sub1_id}/override-score",
        json={"new_score": 98.0, "reason": "Exceptional code clarity"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert override_res.status_code == 200
    assert override_res.json()["score"] == 98.0

    # 10. Class Analytics & CSV Gradebook Export
    analytics_res = client.get(
        f"/api/v1/instructor/courses/{course_id}/analytics",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert analytics_res.status_code == 200
    assert analytics_res.json()["total_submissions"] == 2

    gradebook_res = client.get(
        f"/api/v1/reports/course/{course_id}/gradebook",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert gradebook_res.status_code == 200
    assert "Student One" in gradebook_res.text
    assert "Student Two" in gradebook_res.text
