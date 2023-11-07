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


class PostListSerializer(PostSerializer):
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    numb_of_comments = serializers.IntegerField(read_only=True)
    tags = TagSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Post
        fields = [
            "content",
            "image",
            "tags",
            "created_at",
            "num_of_likes",
            "num_of_dislikes",
            "numb_of_comments",
        ]
