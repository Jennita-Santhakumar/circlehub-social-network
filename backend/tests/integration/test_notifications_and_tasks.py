from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from social.models import Notification, Post
from social.tasks import create_notification, prune_old_notifications, send_notification_email

pytestmark = pytest.mark.django_db


def test_create_notification_task_creates_row(create_user):
    recipient = create_user(username="recip", password="StrongPass123!", email="r@example.com")
    actor = create_user(username="act", password="StrongPass123!", email="ac@example.com")
    post = Post.objects.create(author=recipient, content="p")

    notif_id = create_notification(
        recipient_id=recipient.id, actor_id=actor.id, notification_type="like", post_id=post.id
    )

    assert notif_id is not None
    assert Notification.objects.filter(id=notif_id, recipient=recipient, actor=actor).exists()


def test_create_notification_noop_for_self(create_user):
    user = create_user(username="selfuser", password="StrongPass123!", email="su@example.com")
    result = create_notification(recipient_id=user.id, actor_id=user.id, notification_type="like")
    assert result is None
    assert Notification.objects.count() == 0


def test_send_notification_email_uses_console_backend(create_user):
    recipient = create_user(username="emailrecip", password="StrongPass123!", email="er@example.com")
    actor = create_user(username="emailactor", password="StrongPass123!", email="ea@example.com")

    mail.outbox = []
    send_notification_email(recipient_id=recipient.id, actor_id=actor.id, notification_type="follow")

    assert len(mail.outbox) == 1
    assert recipient.email in mail.outbox[0].to
    assert "emailactor" in mail.outbox[0].subject


def test_prune_old_notifications_deletes_only_old_read(create_user):
    recipient = create_user(username="prunerecip", password="StrongPass123!", email="pr@example.com")
    actor = create_user(username="pruneactor", password="StrongPass123!", email="pa@example.com")

    old_read = Notification.objects.create(
        recipient=recipient, actor=actor, notification_type="like", is_read=True
    )
    Notification.objects.filter(id=old_read.id).update(created_at=timezone.now() - timedelta(days=40))

    recent_read = Notification.objects.create(
        recipient=recipient, actor=actor, notification_type="comment", is_read=True
    )
    old_unread = Notification.objects.create(
        recipient=recipient, actor=actor, notification_type="follow", is_read=False
    )
    Notification.objects.filter(id=old_unread.id).update(created_at=timezone.now() - timedelta(days=40))

    deleted = prune_old_notifications(days=30)

    assert deleted == 1
    remaining_ids = set(Notification.objects.values_list("id", flat=True))
    assert old_read.id not in remaining_ids
    assert recent_read.id in remaining_ids
    assert old_unread.id in remaining_ids


def test_notification_mark_read_endpoint(auth_client, create_user):
    client, user = auth_client()
    actor = create_user(username="markactor", password="StrongPass123!", email="ma@example.com")
    notification = Notification.objects.create(recipient=user, actor=actor, notification_type="follow")

    response = client.post(f"/api/notifications/{notification.id}/mark_read/")

    assert response.status_code == 200
    notification.refresh_from_db()
    assert notification.is_read is True
