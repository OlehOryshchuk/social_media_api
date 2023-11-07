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
            "id",
            "profile_picture",
            "bio",
        ]


class ProfileListSerializer(ProfileSerializer):
    username = serializers.CharField(
        read_only=True, source="user.username"
    )

    class Meta:
        model = Profile,
        fields = [
            "id",
            "username",
            "profile_picture"
        ]


class PostSerializer(serializers.ModelSerializer):
    author = ProfileListSerializer(read_only=True)

    class Meta:
        model = Post,
        fields = [
            "id",
            "author",
            "content",
            "image",
            "tags",
            "created_at"
        ]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "reply_to_comment",
            "created_at"
        ]


class CommentListSerializer(CommentSerializer):
    """See posts comments, and every comment have number
    of likes/dislikes/replies and see who is the author of
    comment"""
    # TODO Make annotations for below 3 fields
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_replies = serializers.IntegerField(read_only=True)
    author = ProfileListSerializer(many=True, read_only=True)

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + [
            "id",
            "author",
            "num_of_likes",
            "num_of_dislikes",
            "num_of_replies"
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PostListSerializer(PostSerializer):
    """List of posts, where we can see number of
    likes/dislikes/comments and post tags"""
    # TODO Make annotations for below 3 fields
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_comments = serializers.IntegerField(read_only=True)
    tags = TagSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "image",
            "tags",
            "created_at",
            "num_of_likes",
            "num_of_dislikes",
            "numb_of_comments",
        ]


class PostDetailSerializer(PostSerializer):
    """See all comments under specific post"""
    comments = CommentListSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "image",
            "tags",
            "created_at",
            "comments"
        ]


class ProfileDetailSerializer(ProfileSerializer):
    """Detail information of current user profile"""
    num_of_followers = serializers.SlugRelatedField(
        read_only=True, sluf_field="num_of_followers"
    )
    num_of_followings = serializers.SlugRelatedField(
        read_only=True, sluf_field="num_of_followings"
    )
    num_of_posts = serializers.SlugRelatedField(
        read_only=True, sluf_field="num_of_posts"
    )
    posts = PostListSerializer(
        many=True, read_only=True
    )

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            "num_of_followers",
            "num_of_followings",
            "num_of_posts",
            "posts",
        ]
