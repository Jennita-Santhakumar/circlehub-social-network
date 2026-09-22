import pytest

from social.models import Comment, Follow, Post, UserProfile

pytestmark = pytest.mark.django_db


def test_create_comment_increments_post_count(auth_client, create_user):
    author = create_user(username="cauthor", password="StrongPass123!", email="ca@example.com")
    post = Post.objects.create(author=author, content="commentable post")
    client, commenter = auth_client(create_user(username="commenter", password="StrongPass123!", email="c@example.com"))

    response = client.post("/api/comments/", {"post": post.id, "content": "nice post!"})

    assert response.status_code == 201
    post.refresh_from_db()
    assert post.comments_count == 1
    assert Comment.objects.filter(post=post, author=commenter).exists()


def test_follow_updates_profile_counts(auth_client, create_user):
    client, follower = auth_client(create_user(username="follower1", password="StrongPass123!", email="f1@example.com"))
    target = create_user(username="target1", password="StrongPass123!", email="t1@example.com")

    response = client.post("/api/follows/", {"following": target.id})
    assert response.status_code == 201

    follower_profile = UserProfile.objects.get(user=follower)
    target_profile = UserProfile.objects.get(user=target)
    assert follower_profile.following_count == 1
    assert target_profile.followers_count == 1


def test_cannot_follow_self(auth_client):
    client, user = auth_client()
    response = client.post("/api/follows/", {"following": user.id})
    assert response.status_code == 400


def test_unfollow_removes_relationship_and_decrements(auth_client, create_user):
    client, follower = auth_client(create_user(username="follower2", password="StrongPass123!", email="f2@example.com"))
    target = create_user(username="target2", password="StrongPass123!", email="t2@example.com")

    create_response = client.post("/api/follows/", {"following": target.id})
    follow_id = create_response.data["id"]

    response = client.delete(f"/api/follows/{follow_id}/")
    assert response.status_code == 204
    assert not Follow.objects.filter(follower=follower, following=target).exists()
    assert UserProfile.objects.get(user=follower).following_count == 0
