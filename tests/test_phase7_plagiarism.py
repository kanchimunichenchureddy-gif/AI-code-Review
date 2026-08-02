from analysis.similarity.engine import similarity_engine
from backend.app.models.user import User, RoleEnum
from backend.app.core.security import get_password_hash


def test_similarity_engine_normalization_and_comparison():
    # Student 1 code
    code1 = """
def calculate_sum(numbers_list):
    total_acc = 0
    for item_val in numbers_list:
        total_acc += item_val
    return total_acc
"""

    # Student 2 code (renamed variables: numbers_list -> data_arr, total_acc -> s, item_val -> x)
    code2 = """
def calculate_sum(data_arr):
    s = 0
    for x in data_arr:
        s += x
    return s
"""

    # Identifier normalization check
    norm1 = similarity_engine.normalize_code(code1)
    norm2 = similarity_engine.normalize_code(code2)
    assert norm1 == norm2

    # Pairwise comparison
    res = similarity_engine.compare_submissions(code1, code2)
    assert res.similarity_score >= 80.0
    assert res.tier in ["HIGH", "Requires Human Review"]
    assert res.human_review_recommended is True


def test_plagiarism_check_api_endpoint(client, test_student, test_instructor, db_session):
    # Create second student
    student2 = User(
        email="bob@university.edu",
        username="bob_student",
        full_name="Bob Student",
        hashed_password=get_password_hash("studentpass123"),
        role=RoleEnum.STUDENT,
        is_active=True,
    )
    db_session.add(student2)
    db_session.commit()

    # Instructor setup course & assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]

    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS1000", "title": "Plagiarism Audit Course"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Sorting Assignment", "language": "python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student 1 submission
    std1_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std1_token = std1_login.json()["access_token"]

    sub1_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "sort.py",
                    "content": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std1_token}"},
    )
    sub1_id = sub1_res.json()["id"]

    # Student 2 submission (nearly identical)
    std2_login = client.post("/api/v1/auth/login", data={"username": "bob_student", "password": "studentpass123"})
    std2_token = std2_login.json()["access_token"]

    sub2_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "sort.py",
                    "content": "def bubble_sort(lst):\n    sz = len(lst)\n    for idx in range(sz):\n        for k in range(0, sz-idx-1):\n            if lst[k] > lst[k+1]:\n                lst[k], lst[k+1] = lst[k+1], lst[k]\n    return lst\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std2_token}"},
    )
    sub2_id = sub2_res.json()["id"]

    # Instructor triggers plagiarism check
    plag_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}/check-plagiarism",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert plag_res.status_code == 200
    plag_data = plag_res.json()
    assert len(plag_data) >= 2  # Pairwise (sub1 -> sub2 and sub2 -> sub1)

    # Student 1 checks plagiarism report
    rep_res = client.get(
        f"/api/v1/submissions/{sub1_id}/plagiarism",
        headers={"Authorization": f"Bearer {std1_token}"},
    )
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert len(rep_data) == 1
    assert rep_data[0]["similarity_score"] >= 70.0
    assert rep_data[0]["human_review_recommended"] is True
