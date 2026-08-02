import io
import zipfile
import pytest
from backend.app.core.storage import StorageManager, StorageSecurityError


def test_create_submission_json(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS500", "title": "Advanced Python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Lab 1", "language": "python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Login & Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub1_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {"filename": "main.py", "content": "def main():\n    print('Hello World')", "language": "python"}
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert sub1_res.status_code == 201
    data1 = sub1_res.json()
    assert data1["attempt_number"] == 1
    assert data1["parent_submission_id"] is None
    assert len(data1["files"]) == 1

    # Second Attempt (Versioning check)
    sub2_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {"filename": "main.py", "content": "def main():\n    print('Hello World 2')", "language": "python"}
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert sub2_res.status_code == 201
    data2 = sub2_res.json()
    assert data2["attempt_number"] == 2
    assert data2["parent_submission_id"] == data1["id"]


def test_create_submission_zip_upload(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS501", "title": "Java Systems"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Java Project", "language": "java"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Login & Zip upload
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("Main.java", "public class Main { public static void main(String[] args) {} }")
        zf.writestr("Utils.java", "public class Utils {}")
        zf.writestr("notes.txt", "Some text file to ignore")

    zip_buffer.seek(0)

    upload_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}/upload",
        files={"file": ("solution.zip", zip_buffer, "application/zip")},
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert len(data["files"]) == 2  # Only .java files extracted
    filenames = [f["filename"] for f in data["files"]]
    assert "Main.java" in filenames
    assert "Utils.java" in filenames


def test_storage_manager_path_traversal_prevention(tmp_path):
    storage = StorageManager(base_dir=tmp_path)
    sub_dir = storage.get_submission_dir(1, 1, 1)

    # Attempt malicious path traversal filename
    with pytest.raises(StorageSecurityError):
        storage.save_file(sub_dir, "../../../etc/passwd", "malicious_content")
