from django.contrib.auth.models import Group
from django.contrib import admin
from .models import (
    Profile,
    Post,
    PostRate,
    Comment,
    CommentRate,
)

admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ["user__username"]
    list_display = ["user", "profile_picture", "bio"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    search_fields = ["author__username"]
    list_display = [
        "author",
        "image",
        "content",
        "created_at",
    ]
    list_filter = ["tags__name"]


admin.site.register(PostRate)
admin.site.register(Comment)
admin.site.register(CommentRate)
