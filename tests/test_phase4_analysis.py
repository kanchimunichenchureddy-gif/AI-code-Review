from analysis.complexity.engine import complexity_engine
from analysis.static.engine import static_analysis_engine


def test_complexity_engine_calculations():
    code = """
def process_data(items):
    total = 0
    for item in items:
        if item > 10:
            if item % 2 == 0:
                total += item
            else:
                total += item * 2
        elif item == 0:
            total += 1
        else:
            total -= 1
    return total
"""
    metrics = complexity_engine.compute_file_metrics("test.py", code, [])
    assert metrics.cyclomatic_complexity >= 5
    assert metrics.cognitive_complexity > 0
    assert metrics.lines_of_code >= 10
    assert metrics.maintainability_index > 0.0
    assert metrics.halstead_volume > 0.0


def test_static_analysis_rule_detections():
    code = """
def bad_function():
    a = 100
    if a > 86400:
        return True
    return False
    print("This is dead code after return")

"""
    findings = static_analysis_engine.analyze_file("bad.py", code, [])
    rule_ids = [f.rule_id for f in findings]
    
    assert "MAGIC_NUMBER" in rule_ids
    assert "POOR_NAMING" in rule_ids
    assert "DEAD_CODE" in rule_ids


def test_full_analysis_endpoint(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS700", "title": "Software Metrics & Static Analysis"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Analysis Assignment", "language": "python"},
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
                    "filename": "analysis_demo.py",
                    "content": "def calculate(val):\n    x = 500\n    if val > 1000:\n        return val * 2\n    return val\n    print('Unreachable')\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Trigger Full Analysis
    analyze_res = client.post(
        f"/api/v1/submissions/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert analyze_res.status_code == 200

    # Query Static Findings
    findings_res = client.get(
        f"/api/v1/submissions/{sub_id}/findings",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0
    rule_ids = [f["rule_id"] for f in findings]
    assert "MAGIC_NUMBER" in rule_ids or "POOR_NAMING" in rule_ids

    # Query Complexity Metrics
    metrics_res = client.get(
        f"/api/v1/submissions/{sub_id}/metrics",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert len(metrics) == 1
    assert metrics[0]["cyclomatic_complexity"] >= 2
