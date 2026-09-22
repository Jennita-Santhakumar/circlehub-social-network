import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_notification_email(recipient_id, actor_id, notification_type, post_id=None):
    """Send an email notification asynchronously, 15s after the triggering event."""
    from django.conf import settings

    try:
        recipient = User.objects.get(id=recipient_id)
        actor = User.objects.get(id=actor_id)
    except User.DoesNotExist:
        logger.warning("send_notification_email: user not found (recipient=%s actor=%s)", recipient_id, actor_id)
        return

    if not recipient.email:
        return

    subject = f"{actor.username} {notification_type}d your post"
    message = (
        f"Hello {recipient.first_name or recipient.username},\n\n"
        f"{actor.username} just {notification_type}d your post on SocialPulse!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient.email], fail_silently=False)


@shared_task
def create_notification(recipient_id, actor_id, notification_type, post_id=None):
    """Create a Notification row, push it live over the user's WebSocket group,
    then schedule the (delayed) email send."""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    from .models import Notification

    if recipient_id == actor_id:
        return None

    notification = Notification.objects.create(
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
    )

    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}",
            {
                "type": "notification.message",
                "data": {
                    "id": notification.id,
                    "notification_type": notification_type,
                    "actor": notification.actor.username,
                    "post_id": post_id,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )

    send_notification_email.apply_async(
        args=[recipient_id, actor_id, notification_type, post_id],
        countdown=15,
    )

    return notification.id


@shared_task
def prune_old_notifications(days=30):
    """Celery Beat periodic task: delete read notifications older than `days`."""
    from .models import Notification

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()
    logger.info("prune_old_notifications: removed %s notifications older than %s days", deleted, days)
    return deleted
