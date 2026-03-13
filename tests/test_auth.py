from fastapi.testclient import TestClient


def test_register_returns_token(client: TestClient, user_credentials: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/register", json=user_credentials)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_returns_token(client: TestClient, user_credentials: dict[str, str]) -> None:
    client.post("/api/v1/auth/register", json=user_credentials)

    response = client.post("/api/v1/auth/login", json=user_credentials)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_returns_400(
    client: TestClient,
    user_credentials: dict[str, str],
) -> None:
    client.post("/api/v1/auth/register", json=user_credentials)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user_credentials["email"], "password": "wrong-password"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Invalid credentials.",
        "error_code": "INVALID_CREDENTIALS",
        "status_code": 400,
    }
