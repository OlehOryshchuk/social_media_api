from rest_framework.reverse import reverse

from rest_framework import serializers
from taggit.serializers import (
    TaggitSerializer,
    TagListSerializerField
)
from taggit.models import Tag

from .models import Profile, Post, PostRate, Comment, CommentRate


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "profile_picture",
            "bio",
        ]


class ProfileListSerializer(ProfileSerializer):
    username = serializers.CharField(read_only=True, source="user.username")
    profile_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:profile-detail",
    )

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "profile_picture",
            "profile_url",
        ]


class ProfileImageUpload(ProfileSerializer):
    """Upload profile picture"""
    class Meta:
        model = Profile
        fields = ["id", "profile_picture"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()

    class Meta:
        model = Post
        fields = ["id", "content", "image", "tags", "created_at"]
        extra_kwargs = {"image": {"required": False}}


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "content", "reply_to_comment", "created_at"]


class CommentListSerializer(CommentSerializer):
    """See posts comments, and every comment have number
    of likes/dislikes/replies and see who is the author of
    comment"""
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_replies = serializers.IntegerField(read_only=True)
    like_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:comment-like",
        lookup_url_kwarg="pk"
    )
    dislike_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:comment-dislike",
        lookup_url_kwarg="pk"
    )
    replies_url = serializers.SerializerMethodField()
    author = ProfileListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "created_at",
            "author",
            "like_url",
            "dislike_url",
            "replies_url",
            "num_of_likes",
            "num_of_dislikes",
            "num_of_replies",
        ]

    def get_replies_url(self, obj: Comment):
        """Return comment replies endpoint URI(Uniform Resource Identifier)"""
        return self.context["request"].build_absolute_uri(
            reverse("social_media:comment-replies", args=[obj.post.id, obj.pk])
        )


class CommentDetailSerializer(CommentSerializer):
    replies = CommentListSerializer(read_only=True, many=True)

    class Meta:
        model = Comment
        fields = ["replies"]


class TagListSerializer(serializers.ModelSerializer):
    tag_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:tag-detail",
    )

    class Meta:
        model = Tag
        fields = ["name", "tag_url"]


class PostListSerializer(PostSerializer):
    """List of posts, where we can see number of
    likes/dislikes/comments and post tags"""

    profile_url = serializers.SerializerMethodField()
    comments_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:post-comments",
        lookup_url_kwarg="post_pk",
    )
    like_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:post-like",
    )
    dislike_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="social_media:post-dislike",
    )
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_comments = serializers.IntegerField(read_only=True)
    tags = TagListSerializer(many=True, read_only=True)

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + [
            "profile_url",
            "tags",
            "comments_url",
            "like_url",
            "dislike_url",
            "num_of_likes",
            "num_of_dislikes",
            "num_of_comments",
        ]

    def get_profile_url(self, obj: Post):
        """Return profile detail URI(Uniform Resource Identifier)"""
        return self.context["request"].build_absolute_uri(
            reverse("social_media:profile-detail", args=[obj.author.id])
        )


class ProfileDetailSerializer(ProfileSerializer):
    """Detail information of current user profile"""

    num_of_followers = serializers.IntegerField(read_only=True)
    num_of_followings = serializers.IntegerField(read_only=True)
    num_of_posts = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    posts = serializers.HyperlinkedIdentityField(
        view_name="social_media:post-profile",
        read_only=True,
    )

    def get_is_following(self, obj):
        """Return True if user is following current profile else False"""
        user = self.context["request"].user
        return user.profile.followings.filter(id=obj.id).exists()

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            "is_following",
            "num_of_followers",
            "num_of_followings",
            "num_of_posts",
            "posts",
        ]
