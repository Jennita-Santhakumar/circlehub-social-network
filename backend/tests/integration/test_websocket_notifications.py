"""Integration test for the real-time notification flow: exercises the actual
Channels WebSocket consumer over the real (Redis-backed) channel layer, using
Channels' WebsocketCommunicator testing utility - not a mock.
"""

import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from config.asgi import application

pytestmark = pytest.mark.django_db


@pytest.mark.asyncio
async def test_unauthenticated_connection_is_rejected():
    communicator = WebsocketCommunicator(application, "/ws/notifications/")
    connected, _ = await communicator.connect()
    assert connected is False
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_authenticated_user_receives_group_notification(create_user):
    user = await sync_create_user(create_user)
    token = str(RefreshToken.for_user(user).access_token)

    communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
    connected, _ = await communicator.connect()
    assert connected is True

    greeting = await communicator.receive_json_from()
    assert greeting["type"] == "connected"

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user.id}",
        {
            "type": "notification.message",
            "data": {"id": 1, "notification_type": "like", "actor": "someone"},
        },
    )

    response = await communicator.receive_json_from(timeout=5)
    assert response["type"] == "notification"
    assert response["data"]["notification_type"] == "like"
    assert response["data"]["actor"] == "someone"

    await communicator.disconnect()


async def sync_create_user(create_user):
    from asgiref.sync import sync_to_async

    return await sync_to_async(create_user)(
        username="wsuser", password="StrongPass123!", email="ws@example.com"
    )
