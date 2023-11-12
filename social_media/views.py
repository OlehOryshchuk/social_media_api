from abc import ABC, abstractmethod

from django.db.models import (
    Q,
    Count,
    QuerySet,
)
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import status, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter

from taggit.models import Tag

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
# TODO create permission that check if current user is owner
# TODO of that profile
# TODO create Post method to reteive posts of profile id using action decorator


class LikeDislikeObjectMixin(ABC):
    @abstractmethod
    def _like_dislike_or_remove(self, request, like_value: bool):
        pass

    @action(
        methods=["post"],
        detail=True,
        url_path="like"
    )
    def like_unlike(self, request, pk):
        """Like or unlike post"""
        self._like_dislike_or_remove(request, True)
        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=True,
        url_path="dislike"
    )
    def dislike_remove_dislike(self, request, pk):
        """DisLike post or remove dislike"""
        self._like_dislike_or_remove(request, False)
        return Response(status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.ModelViewSet):
    # TODO add filter by username
    serializer_class = ProfileSerializer
    queryset = Profile.objects.select_related(
        "user"
    ).prefetch_related(
        "posts", "followings"
    ).annotate(
        num_of_followers=Count("followers"),
        num_of_followings=Count("followings"),
        num_of_posts=Count("posts"),
    )

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "posts__comments"
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProfileDetailSerializer

        if self.action in ["list", "followings", "followers"]:
            return ProfileListSerializer

        if self.action == "upload_profile_picture":
            return ProfileImageUpload

        if self.action == "profile_posts":
            return PostListSerializer

        return ProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        methods=["get"],
        detail=True,
        url_name="follow_unfollow"
    )
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

    @action(
        methods=["get"],
        detail=True,
    )
    def followings(self, request, pk=None):
        """Return list of profiles current profile is following"""
        profile = self.get_object()
        following = profile.followings.all()

        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=True,
    )
    def followers(self, request, pk=None):
        """Return list of profiles that are following current profile"""
        profile = self.get_object()
        followers = profile.followers.all()

        serializer = self.get_serializer(followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=True,
    )
    def upload_profile_picture(self, request, pk=None):
        """Upload profile image on current profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=True,
        url_path="posts",
        url_name="posts"
    )
    def profile_posts(self, request, pk):
        """Return Profile posts"""
        profile = self.get_object()
        data = profile.posts.all()
        serializer = self.get_serializer(data, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(
    LikeDislikeObjectMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """View for Creating/Delete/Update/List actions & also
    like post/dislike or remove reaction from post & see all profiles
    who disliked or liked specific profile"""
    queryset = Post.objects.select_related(
        "author"
    ).prefetch_related(
        "likes", "comments", "tags"
    )
    serializer_class = PostSerializer
    pagination_class = CustomPagination
    rate_model = PostRate

    def get_queryset(self):
        queryset = self.queryset
        # If following_posts then return current user
        # followings posts
        current_profile = self.request.user.profile
        following_posts: bool = self.request.query_params.get("following_posts", None)

        if following_posts:
            queryset = current_profile.followings.all()

        days_ago = settings.POST_CREATED_AT_DAYS_AGO
        days_ago = timezone.now() - timezone.timedelta(days=days_ago)

        return queryset.annotate(
            num_of_likes=Count(
                "postrate",
                filter=Q(postrate__like=True)
            ),
            num_of_dislikes=Count(
                "postrate",
                filter=Q(postrate__like=False)
            ),
            num_of_comments=Count(
                "comments__id",
            ),
        ).order_by(
            "-num_of_likes",
            "num_of_dislikes",
        ).filter(
            created_at__gt=days_ago
        )

    def get_serializer_class(self):
        if self.action in ("profiles_liked", "profiles_disliked"):
            return ProfileListSerializer

        if self.action == "list":
            return PostListSerializer

        if self.action == "profile_posts":
            return ProfileDetailSerializer

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

        if post_rate:
            if post_rate.like == like_value:
                # Remove our reaction to post
                post_rate.remove()

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
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=True,
    )
    def profiles_liked(self, request, pk):
        """Return profiles who liked post"""
        self._get_post_profiles_who_likes_or_dislikes(request, True)

    @action(
        methods=["post"],
        detail=True,
    )
    def profiles_disliked(self, request, pk):
        """Return profiles who disliked post"""
        self._get_post_profiles_who_likes_or_dislikes(request, False)

    @action(
        methods=["get"],
        detail=True,
        url_path="profile",
        url_name="profile-posts"
    )
    def profile_posts(self, request, pk):
        """Return profiles post"""
        profile = get_object_or_404(Profile, id=pk)
        data = profile.posts.all()
        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(
    LikeDislikeObjectMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CommentSerializer

    def get_object(self):
        """Will return post object where we can later get all comments
        or if comment_id was passed than return post specific comment"""
        post_pk = self.kwargs.get("pk")
        post = get_object_or_404(Post, post_pk)
        comment_pk = self.kwargs.get("comment_pk")

        if comment_pk:
            try:
                return post.comments.get(id=comment_pk)
            except Comment.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        return post

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)

    def get_queryset(self):
        """Return Post comments or comment replies"""
        # if post is returned by get_objects than use comments attribute
        # if specific comment returned then use attribute reply_to_comment
        queryset = getattr(self.get_object(), "comments", "reply_to_comment").select_related(
            "author", "post", "reply_to_comment"
        ).prefetch_related("likes")

        return queryset.annotate(
            num_of_likes=Count(
                "commentrate_set",
                filter=Q(commentrate_set__like=True)
            ),
            num_of_dislikes=Count(
                "commentrate_set",
                filter=Q(commentrate_set__like=False)
            ),
            num_of_replies=Count(
                "reply_to_comment",
            ),
        ).order_by(
            "-num_of_likes",
            "num_of_dislikes",
            "-num_of_replies",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CommentListSerializer

        if self.action == "retrieve":
            return CommentDetailSerializer

        return CommentSerializer

    def _like_dislike_or_remove(self, request, like_value: bool) -> None:
        """Like, dislike, or remove both"""
        comment = self.get_object()
        current_profile = request.user.profile

        comment_rate, created = CommentRate.objects.get_or_create(
            comment=comment, profile=current_profile, defaults={"like": like_value}
        )

        if comment_rate:
            if comment_rate.like == like_value:
                # Remove our reaction to comment
                comment_rate.remove()

            else:
                comment_rate.like = like_value

        comment_rate.save()


class TagViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Get list/create tags"""
    serializer_class = TagSerializer
    queryset = Tag.objects.prefetch_related(
        "posts",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return TagListSerializer

        return TagSerializer
