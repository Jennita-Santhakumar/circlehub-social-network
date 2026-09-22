from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    FollowViewSet,
    MeView,
    NotificationViewSet,
    PostViewSet,
    RegisterView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"follows", FollowViewSet, basename="follow")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
