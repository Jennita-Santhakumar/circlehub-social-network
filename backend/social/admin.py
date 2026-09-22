from django.contrib import admin

from .models import Comment, Follow, Like, Notification, Post, UserProfile

admin.site.register(UserProfile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Notification)
