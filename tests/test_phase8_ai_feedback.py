from ai.validator.evidence_validator import evidence_validator, FeedbackCandidate
from ai.service import ai_feedback_service
from backend.app.models.submission import SubmissionFile
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel


def test_evidence_validator_guardrail_rejections():
    files = [
        SubmissionFile(id=1, filename="main.py", content="x = 10\nprint(x)\n", language="python")
    ]
    static_findings = [
        StaticFindingModel(id=1, file_path="main.py", rule_id="POOR_NAMING", category="Style", severity="LOW", message="Poor name", line_start=1, line_end=1)
    ]
    security_findings = []

    # Valid candidate (matches line 1 in main.py)
    valid_cand = FeedbackCandidate(
        category="Style", title="Naming", what_text="a", why_text="b", how_to_fix_text="c", example_code=None, file_path="main.py", line_number=1
    )
    assert evidence_validator.validate_candidate(valid_cand, files, static_findings, security_findings) is True

    # Hallucinated line number (Line 999 does not exist in 2-line file)
    hallucinated_line_cand = FeedbackCandidate(
        category="Style", title="Naming", what_text="a", why_text="b", how_to_fix_text="c", example_code=None, file_path="main.py", line_number=999
    )
    assert evidence_validator.validate_candidate(hallucinated_line_cand, files, static_findings, security_findings) is False

    # Hallucinated file path (nonexistent_file.py does not exist)
    hallucinated_file_cand = FeedbackCandidate(
        category="Style", title="Naming", what_text="a", why_text="b", how_to_fix_text="c", example_code=None, file_path="nonexistent_file.py", line_number=1
    )
    assert evidence_validator.validate_candidate(hallucinated_file_cand, files, static_findings, security_findings) is False


def test_ai_feedback_generation_api_integration(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS1100", "title": "AI Feedback & Pedagogical Systems"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Feedback Lab", "language": "python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Submission with vulnerabilities & smells
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "demo.py",
                    "content": "import os\ndef execute(cmd):\n    a = 100\n    if a > 86400:\n        os.system('ls ' + cmd)\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Trigger AI Feedback Generation
    gen_res = client.post(
        f"/api/v1/submissions/{sub_id}/generate-feedback",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert gen_res.status_code == 200
    feedback_cards = gen_res.json()
    assert len(feedback_cards) > 0

    # Verify 4-Part Structure on generated feedback cards
    first_card = feedback_cards[0]
    assert "what_text" in first_card
    assert "why_text" in first_card
    assert "how_to_fix_text" in first_card

    # Retrieve Feedback via GET endpoint
    get_fb_res = client.get(
        f"/api/v1/submissions/{sub_id}/feedback",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert get_fb_res.status_code == 200
    assert len(get_fb_res.json()) == len(feedback_cards)
