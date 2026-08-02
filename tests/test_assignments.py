def test_create_assignment_and_rubric(client, test_instructor):
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "prof_miller", "password": "securepass123"},
    )
    token = login_res.json()["access_token"]

    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS301", "title": "Software Engineering"},
        headers={"Authorization": f"Bearer {token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={
            "title": "Project 1: Binary Tree",
            "description": "Implement insert and traversal",
            "language": "python",
            "max_score": 100,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert assign_res.status_code == 201
    assign_id = assign_res.json()["id"]

    rubric_res = client.post(
        f"/api/v1/rubrics/assignment/{assign_id}",
        json={
            "title": "Binary Tree Rubric",
            "rules": [
                {
                    "rule_code": "R_NAMING",
                    "category": "Style",
                    "weight": 20.0,
                    "penalty_per_violation": 2.0,
                    "max_deduction": 20.0,
                    "is_mandatory": False,
                },
                {
                    "rule_code": "R_COMPLEXITY",
                    "category": "Performance",
                    "weight": 30.0,
                    "penalty_per_violation": 10.0,
                    "max_deduction": 30.0,
                    "is_mandatory": True,
                },
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rubric_res.status_code == 201
    rubric_data = rubric_res.json()
    assert len(rubric_data["rules"]) == 2
