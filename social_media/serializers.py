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
    profile_url = serializers.HyperlinkedIdentityField(
        view_name="profile-detail",
        lookup_field="author__id",
        read_only=True
    )

    class Meta:
        model = Profile,
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


class PostSerializer(serializers.ModelSerializer):

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

    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_replies = serializers.IntegerField(read_only=True)
    replies_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="comments-detail",
        lookup_field="id"
    )
    author = ProfileListSerializer(many=True, read_only=True)

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + [
            "id",
            "author",
            "num_of_likes",
            "num_of_dislikes",
            "num_of_replies"
        ]


class CommentDetailSerializer(CommentSerializer):
    replies = CommentListSerializer(
        read_only=True, many=True
    )

    class Meta:
        model = Comment
        fields = ["replies"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class TagListSerializer(TagSerializer):
    detail_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="tag-detail",
    )

    class Meta:
        model = Tag
        fields = ["id", "name", "tag_url"]


class PostListSerializer(PostSerializer):
    """List of posts, where we can see number of
    likes/dislikes/comments and post tags"""
    comments_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="post-comments",
        lookup_field="id"
    )
    like_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="post-like",
        lookup_field="id"
    )
    dislike_url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name="post-like",
        lookup_field="id"
    )
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_dislikes = serializers.IntegerField(read_only=True)
    num_of_comments = serializers.IntegerField(read_only=True)
    tags = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="tag_detail"
    )

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + [
            "profile_url",
            "comments_url",
            "like_url",
            "dislike_url",
            "num_of_likes",
            "num_of_dislikes",
            "numb_of_comments",
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
    is_following = serializers.SerializerMethodField()
    posts = serializers.HyperlinkedIdentityField(
        view_name="profile-posts",
        read_only=True
    )

    def get_is_following(self, obj):
        """Return True if user is following current profile else False"""
        user = self.context["request"].user
        return user.profile.followings.filter(id=obj.id).exists()

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            "num_of_followers",
            "num_of_followings",
            "num_of_posts",
            "posts",
        ]
