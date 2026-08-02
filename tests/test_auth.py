def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newstudent@univ.edu",
            "username": "newstudent",
            "full_name": "New Student",
            "password": "Password123!",
            "role": "STUDENT",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@univ.edu"
    assert data["username"] == "newstudent"
    assert "id" in data


def test_login_user(client, test_student):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "alex_student",
            "password": "studentpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user_me(client, test_student):
    login_res = client.post(
        "/api/v1/auth/login",
        data={
            "username": "alex_student",
            "password": "studentpass123",
        },
    )
    token = login_res.json()["access_token"]
    
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "alex@university.edu"
    assert data["role"] == "STUDENT"
