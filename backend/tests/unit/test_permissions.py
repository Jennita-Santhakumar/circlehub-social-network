from unittest.mock import Mock

from social.permissions import IsOwnerOrReadOnly


def test_safe_method_always_allowed():
    perm = IsOwnerOrReadOnly()
    request = Mock(method="GET", user=Mock())
    obj = Mock(author=Mock())
    assert perm.has_object_permission(request, None, obj) is True


def test_owner_can_write():
    perm = IsOwnerOrReadOnly()
    user = Mock()
    request = Mock(method="DELETE", user=user)
    obj = Mock(author=user)
    assert perm.has_object_permission(request, None, obj) is True


def test_non_owner_cannot_write():
    perm = IsOwnerOrReadOnly()
    request = Mock(method="DELETE", user=Mock())
    obj = Mock(author=Mock())
    assert perm.has_object_permission(request, None, obj) is False


def test_falls_back_to_user_attr_when_no_author():
    perm = IsOwnerOrReadOnly()
    user = Mock()
    request = Mock(method="PUT", user=user)
    obj = Mock(spec=["user"], user=user)
    assert perm.has_object_permission(request, None, obj) is True
