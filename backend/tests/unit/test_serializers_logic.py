from unittest.mock import Mock

from social.serializers import PostSerializer


def test_is_liked_false_when_unauthenticated():
    post = Mock()
    request = Mock()
    request.user.is_authenticated = False
    serializer = PostSerializer(context={"request": request})
    assert serializer.get_is_liked(post) is False


def test_is_liked_false_when_no_request():
    post = Mock()
    serializer = PostSerializer(context={})
    assert serializer.get_is_liked(post) is False


def test_is_liked_true_when_like_exists():
    request = Mock()
    request.user.is_authenticated = True
    post = Mock()
    post.likes.filter.return_value.exists.return_value = True
    serializer = PostSerializer(context={"request": request})
    assert serializer.get_is_liked(post) is True
