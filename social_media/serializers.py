from rest_framework.serializers import ModelSerializer

from .models import (
    Profile,
    Post,
    PostRate,
    Comment,
    CommentRate
)


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "username",
            "profile_picture",
            "bio",
        ]


class PostSerializer(ModelSerializer):
    class Meta:
        model = Post,
        fields = [
            "content",
            "image",
            "tags"
        ]


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "content",
            "reply_to_comment"
        ]
