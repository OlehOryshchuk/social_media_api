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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            "user",
        )

        return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    search_fields = ["author__user__username", "tags__name"]
    list_display = [
        "author",
        "image",
        "content",
        "get_tags",
        "created_at",
    ]

    @staticmethod
    def get_tags(obj):
        tags = []
        for tag in obj.tags.all():
            tags.append(str(tag))
        return ", ".join(tags)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            "author__user"
        ).prefetch_related("tags")

        return queryset


admin.site.register(PostRate)
admin.site.register(Comment)
admin.site.register(CommentRate)
