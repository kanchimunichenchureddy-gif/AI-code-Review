from backend.app.models.user import User, RoleEnum
from reports.export_service import report_export_service


def test_course_analytics_and_gradebook_export(client, test_student, test_instructor, db_session):
    # Instructor setup course & assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]

    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS1200", "title": "Dashboard & Reporting Systems"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Dashboard Project", "language": "python", "max_score": 100},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "app.py",
                    "content": "def main():\n    print('Hello World')\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Trigger Full Analysis
    client.post(f"/api/v1/submissions/{sub_id}/analyze", headers={"Authorization": f"Bearer {std_token}"})

    # Test Instructor Analytics Endpoint
    analytics_res = client.get(
        f"/api/v1/instructor/courses/{course_id}/analytics",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["course_code"] == "CS1200"
    assert analytics_data["total_submissions"] == 1

    # Test CSV Gradebook Download Endpoint
    csv_res = client.get(
        f"/api/v1/reports/course/{course_id}/gradebook",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Alex Student" in csv_res.text

    # Test JSON Submission Report Export Endpoint
    json_res = client.get(
        f"/api/v1/reports/submission/{sub_id}/export",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert json_res.status_code == 200
    report_data = json_res.json()
    assert report_data["student_name"] == "Alex Student"
    assert "complexity_metrics" in report_data


def test_instructor_score_override_api(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]

    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS1300", "title": "Grade Override Testing"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Override Assignment", "language": "python", "max_score": 100},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "calc.py",
                    "content": "x = 10\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Instructor overrides score
    override_res = client.post(
        f"/api/v1/instructor/submissions/{sub_id}/override-score",
        json={"new_score": 92.5, "reason": "Bonus points awarded for clean structure"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert override_res.status_code == 200
    assert override_res.json()["score"] == 92.5
