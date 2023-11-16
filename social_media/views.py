from abc import ABC, abstractmethod

from django.db.models import (
    Q,
    Count,
    QuerySet,
)
from django.shortcuts import get_object_or_404

from rest_framework import status, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter

from taggit.models import Tag
from taggit.serializers import (
    TaggitSerializer
)

from .paginations import CustomPagination
from .serializers import (
    TagSerializer,
    TagListSerializer,
    PostSerializer,
    PostListSerializer,
    CommentSerializer,
    CommentListSerializer,
    CommentDetailSerializer,
    ProfileSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileImageUpload,
)

from .models import (
    Profile,
    Post,
    PostRate,
    Comment,
    CommentRate,
)

from .view_utils import (
    LikeDislikeObjectMixin,
    count_likes_dislikes,
)

# TODO create permission that check if current user is owner
# TODO of that profile
# TODO create Post method to reteive posts of profile id using action decorator


class ProfileViewSet(viewsets.ModelViewSet):
    # TODO add filter by username
    serializer_class = ProfileSerializer
    queryset = (
        Profile.objects.select_related("user")
        .prefetch_related("posts", "followings")
        .annotate(
            num_of_followers=Count("followers"),
            num_of_followings=Count("followings"),
            num_of_posts=Count("posts"),
        )
    )

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("posts__comments")

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProfileDetailSerializer

        if self.action in ["list", "followings", "followers"]:
            return ProfileListSerializer

        if self.action == "upload_profile_picture":
            return ProfileImageUpload

        return ProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=["get"], detail=True, url_name="follow_unfollow")
    def follow_or_unfollow(self, request, pk=None):
        """Follow or unfollow profile by current profile"""
        profile = self.get_object()
        current_profile: Profile = request.user.profile

        # check if current prf is following another prf
        is_following = current_profile.followings.filter(id=profile.id).exists()

        if is_following:
            # unfollow profile
            current_profile.followings.remove(profile)
            return Response({"unfollow": "Unfollow successful"})

        # follow profile
        current_profile.followings.add(profile)
        return Response({"follow": "Follow successful"}, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True,)
    def followings(self, request, pk=None):
        """Return list of profiles current profile is following"""
        profile = self.get_object()
        following = profile.followings.all()

        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True,)
    def followers(self, request, pk=None):
        """Return list of profiles that are following current profile"""
        profile = self.get_object()
        followers = profile.followers.all()

        serializer = self.get_serializer(followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True,)
    def upload_profile_picture(self, request, pk=None):
        """Upload profile image on current profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(
    LikeDislikeObjectMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """View for Creating/Delete/Update/List actions & also
    like post/dislike or remove reaction from post & see all profiles
    who disliked or liked specific profile"""

    queryset = Post.objects.select_related("author").prefetch_related(
        "likes", "comments", "tags"
    )
    serializer_class = PostSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        current_profile = self.request.user.profile
        # If following_posts then return current user followings posts
        following_posts: bool = self.request.query_params.get("following_posts", None)

        if following_posts:
            queryset = current_profile.followings.all()

        return count_likes_dislikes(
                queryset, "postrate"
        ).annotate(
            num_of_comments=Count("comments")
        ).order_by("-created_at", "num_of_comments")

    def get_serializer_class(self):
        if self.action in (
                "profiles_liked",
                "profiles_disliked",
                "profile_posts",
                "list",

        ):
            return PostListSerializer

        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)

    def _like_dislike_or_remove(self, request, like_value: bool) -> None:
        """Like, dislike, or remove both"""
        post = self.get_object()
        current_profile = request.user.profile

        post_rate, created = PostRate.objects.get_or_create(
            post=post, profile=current_profile, defaults={"like": like_value}
        )

        if not created:
            if post_rate.like == like_value:
                # Remove our reaction to post
                post_rate.delete()
            else:
                post_rate.like = like_value
                post_rate.save()

    def _get_post_profiles_who_likes_or_dislikes(self, request, like_value: bool):
        """Return profiles that liked or disliked post"""
        post = self.get_object()

        try:
            data = PostRate.objects.get(post=post).filter(like=like_value)
        except PostRate.DoesNotExist:
            return Response(
                {"post_error": "Post Does Not Exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True,)
    def profiles_liked(self, request, pk):
        """Return profiles who liked post"""
        self._get_post_profiles_who_likes_or_dislikes(request, True)

    @action(methods=["get"], detail=True, url_name="profile-disliked")
    def profiles_disliked(self, request, pk):
        """Return profiles who disliked post"""
        self._get_post_profiles_who_likes_or_dislikes(request, False)

    @action(methods=["get"], detail=True, url_path="profile", url_name="profile")
    def profile_posts(self, request, pk):
        """Accept profile pk and return profile posts"""
        profile = get_object_or_404(Profile, id=pk)
        data = Post.objects.filter(author=profile)

        annotate = count_likes_dislikes(data, "postrate").annotate(
            num_of_comments=Count("comments"),
        ).order_by("-num_of_comments")

        serializer = self.get_serializer(annotate, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(
    LikeDislikeObjectMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """List comments under post pk, Detail - return replies under comment
    Create/Update/Delete comment"""

    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_post(self):
        return get_object_or_404(Post, pk=self.kwargs.get("post_pk"))

    def get_comment(self):
        """Return Comment instance using comment pk"""
        return get_object_or_404(Comment, id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile, post=self.get_post())

    @staticmethod
    def annotate_queryset(queryset: QuerySet) -> QuerySet:
        queryset = count_likes_dislikes(
                queryset, "commentrate"
        ).annotate(
            num_of_replies=Count("replies"),
        ).order_by("-num_of_replies")

        return queryset

    def get_comments(self):
        """Return Post comments"""
        queryset = Comment.objects.filter(post=self.get_post())
        return self.annotate_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "list":
            return CommentListSerializer

        if self.action == "retrieve":
            return CommentDetailSerializer

        return CommentSerializer

    def _like_dislike_or_remove(self, request, like_value: bool) -> None:
        """Like, dislike, or remove both"""
        comment = self.get_comment()
        current_profile = request.user.profile

        comment_rate, created = CommentRate.objects.get_or_create(
            comment=comment, profile=current_profile, defaults={"like": like_value}
        )

        if not created:
            if comment_rate.like == like_value:
                # Remove our reaction to comment
                comment_rate.delete()

            else:
                comment_rate.like = like_value
                comment_rate.save()

    def list(self, request, post_pk: int):
        """GET comments under post"""
        comments = self.get_comments()
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Get list/create tags, and detail endpoint will return
    posts under tag id"""

    serializer_class = TaggitSerializer
    queryset = Tag.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TagListSerializer

        if self.action == "retrieve":
            return PostListSerializer

        return TaggitSerializer

    def retrieve(self, request, pk):
        """Return posts under tag pk"""
        tag = get_object_or_404(Tag, id=pk)
        data = Post.objects.filter(tags__id=tag.id)

        annotate = count_likes_dislikes(data, "postrate").annotate(
            num_of_comments=Count("comments")
        ).order_by("num_of_comments")

        serializer = self.get_serializer(annotate, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
