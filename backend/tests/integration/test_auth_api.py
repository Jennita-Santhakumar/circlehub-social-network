import pytest
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


def test_register_creates_user_and_profile(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {"username": "newuser", "password": "StrongPass123!", "email": "n@example.com"},
    )
    assert response.status_code == 201
    user = User.objects.get(username="newuser")
    assert user.userprofile is not None


def test_token_obtain_and_refresh(api_client, create_user):
    create_user(username="bob", password="StrongPass123!")
    response = api_client.post("/api/auth/token/", {"username": "bob", "password": "StrongPass123!"})
    assert response.status_code == 200
    assert "access" in response.data and "refresh" in response.data

    refresh_response = api_client.post("/api/auth/token/refresh/", {"refresh": response.data["refresh"]})
    assert refresh_response.status_code == 200
    assert "access" in refresh_response.data


def test_me_requires_auth(api_client):
    response = api_client.get("/api/auth/me/")
    assert response.status_code == 401


def test_me_returns_current_user(auth_client):
    client, user = auth_client()
    response = client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["username"] == user.username
