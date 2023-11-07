from rest_framework import serializers
from taggit.models import Tag

from .models import (
    Profile,
    Post,
    PostRate,
    Comment,
    CommentRate
)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "username",
            "profile_picture",
            "bio",
        ]


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post,
        fields = [
            "content",
            "image",
            "tags",
            "created_at"
        ]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "content",
            "reply_to_comment",
            "created_at"
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]

