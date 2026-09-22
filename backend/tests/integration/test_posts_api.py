import pytest

from social.models import Notification, Post

pytestmark = pytest.mark.django_db


def test_create_post(auth_client):
    client, user = auth_client()
    response = client.post("/api/posts/", {"content": "hello world"})
    assert response.status_code == 201
    assert Post.objects.filter(author=user, content="hello world").exists()


def test_like_post_increments_count_and_notifies(auth_client, create_user):
    author = create_user(username="author", password="StrongPass123!", email="a@example.com")
    post = Post.objects.create(author=author, content="my post")

    client, liker = auth_client(create_user(username="liker", password="StrongPass123!", email="l@example.com"))
    response = client.post(f"/api/posts/{post.id}/like/")

    assert response.status_code == 200
    post.refresh_from_db()
    assert post.likes_count == 1
    assert Notification.objects.filter(recipient=author, actor=liker, notification_type="like").exists()


def test_unlike_post_decrements_count(auth_client, create_user):
    author = create_user(username="author2", password="StrongPass123!", email="a2@example.com")
    post = Post.objects.create(author=author, content="another post")
    client, _ = auth_client(create_user(username="liker2", password="StrongPass123!", email="l2@example.com"))

    client.post(f"/api/posts/{post.id}/like/")
    response = client.post(f"/api/posts/{post.id}/unlike/")

    assert response.status_code == 200
    post.refresh_from_db()
    assert post.likes_count == 0


def test_feed_returns_only_followed_authors_posts(auth_client, create_user):
    client, me = auth_client(create_user(username="me", password="StrongPass123!", email="me@example.com"))
    followed = create_user(username="followed", password="StrongPass123!", email="f@example.com")
    stranger = create_user(username="stranger", password="StrongPass123!", email="s@example.com")

    Post.objects.create(author=followed, content="from followed")
    Post.objects.create(author=stranger, content="from stranger")

    client.post("/api/follows/", {"following": followed.id})
    response = client.get("/api/posts/feed/")

    assert response.status_code == 200
    contents = [p["content"] for p in response.data]
    assert "from followed" in contents
    assert "from stranger" not in contents


def test_double_like_is_idempotent(auth_client, create_user):
    author = create_user(username="author3", password="StrongPass123!", email="a3@example.com")
    post = Post.objects.create(author=author, content="post3")
    client, _ = auth_client(create_user(username="liker3", password="StrongPass123!", email="l3@example.com"))

    client.post(f"/api/posts/{post.id}/like/")
    response = client.post(f"/api/posts/{post.id}/like/")

    assert response.data["liked"] is False
    post.refresh_from_db()
    assert post.likes_count == 1
