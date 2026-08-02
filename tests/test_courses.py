def test_create_course_instructor(client, test_instructor):
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "prof_miller", "password": "securepass123"},
    )
    token = login_res.json()["access_token"]

    response = client.post(
        "/api/v1/courses/",
        json={
            "code": "CS101",
            "title": "Intro to Computer Science",
            "description": "Foundations of Python & Algorithms",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "CS101"
    assert data["instructor_id"] == test_instructor.id


def test_enroll_student_in_course(client, test_instructor, test_student):
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "prof_miller", "password": "securepass123"},
    )
    token = login_res.json()["access_token"]

    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS201", "title": "Data Structures"},
        headers={"Authorization": f"Bearer {token}"},
    )
    course_id = course_res.json()["id"]

    enroll_res = client.post(
        f"/api/v1/courses/{course_id}/enroll",
        json={"user_email": "alex@university.edu"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert enroll_res.status_code == 200
