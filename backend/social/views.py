from django.contrib.auth.models import User
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Comment, Follow, Like, Notification, Post
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CommentSerializer,
    FollowSerializer,
    NotificationSerializer,
    PostSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tasks import create_notification


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("comments__author").all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_permissions(self):
        if self.action in ("like", "unlike", "feed", "list", "retrieve", "create"):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            post.likes_count += 1
            post.save(update_fields=["likes_count"])
            create_notification.delay(
                recipient_id=post.author_id,
                actor_id=request.user.id,
                notification_type="like",
                post_id=post.id,
            )
        return Response({"liked": created, "likes_count": post.likes_count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        post = self.get_object()
        like = Like.objects.filter(user=request.user, post=post).first()
        if like:
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save(update_fields=["likes_count"])
        return Response({"unliked": True, "likes_count": post.likes_count})

    @action(detail=False, methods=["get"])
    def feed(self, request):
        following_ids = Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
        posts = self.get_queryset().filter(author_id__in=following_ids).order_by("-created_at")[:50]
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.select_related("author", "post").all()
        post_id = self.request.query_params.get("post")
        if post_id:
            qs = qs.filter(post_id=post_id)
        return qs

    def perform_create(self, serializer):
        post = serializer.validated_data["post"]
        comment = serializer.save(author=self.request.user)
        post.comments_count += 1
        post.save(update_fields=["comments_count"])
        create_notification.delay(
            recipient_id=post.author_id,
            actor_id=self.request.user.id,
            notification_type="comment",
            post_id=post.id,
        )
        return comment


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Follow.objects.select_related("follower", "following").filter(follower=self.request.user)

    def create(self, request, *args, **kwargs):
        following_id = request.data.get("following")
        if not following_id:
            return Response({"detail": "following is required"}, status=status.HTTP_400_BAD_REQUEST)
        if int(following_id) == request.user.id:
            return Response({"detail": "cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        target = generics.get_object_or_404(User, id=following_id)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created:
            from .models import UserProfile

            follower_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            following_profile, _ = UserProfile.objects.get_or_create(user=target)
            follower_profile.following_count += 1
            follower_profile.save(update_fields=["following_count"])
            following_profile.followers_count += 1
            following_profile.save(update_fields=["followers_count"])
            create_notification.delay(
                recipient_id=target.id,
                actor_id=request.user.id,
                notification_type="follow",
            )
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        from .models import UserProfile

        follower_profile, _ = UserProfile.objects.get_or_create(user=instance.follower)
        following_profile, _ = UserProfile.objects.get_or_create(user=instance.following)
        follower_profile.following_count = max(0, follower_profile.following_count - 1)
        follower_profile.save(update_fields=["following_count"])
        following_profile.followers_count = max(0, following_profile.followers_count - 1)
        following_profile.save(update_fields=["followers_count"])
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.select_related("actor", "recipient").filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read": updated})
