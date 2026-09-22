"""Shared test fixtures.

Unit tests (tests/unit) avoid the database where possible. Integration tests
(tests/integration) hit real Postgres/Redis via pytest-django's `db` fixture
and a real channel layer - never mocks. Env var defaults below mirror
docker-compose / CI service settings so `pytest` works locally and in CI
without extra setup.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("POSTGRES_DB", "socialpulse_test")
os.environ.setdefault("POSTGRES_USER", "socialpulse")
os.environ.setdefault("POSTGRES_PASSWORD", "socialpulse")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-do-not-use-in-production")

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create(username="alice", password="StrongPass123!", email="alice@example.com"):
        return User.objects.create_user(username=username, password=password, email=email)

    return _create


@pytest.fixture
def auth_client(db, create_user):
    def _auth(user=None):
        user = user or create_user()
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return client, user

    return _auth
