from django.db.models import (
    Q,
    Count,
    QuerySet,
)
from django.utils import timezone
from django.conf import settings

from rest_framework import status, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from taggit.models import Tag

from .paginations import CustomPagination
from .serializers import (
    PostSerializer,
    PostListSerializer,

    CommentSerializer,
    CommentListSerializer,

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


class ProfileViewSet(viewsets.ModelViewSet):
    # TODO add filter by username
    serializer_class = ProfileSerializer
    queryset = Profile.objects.select_related(
        "user"
    ).prefetch_related("posts", "followings")

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

        if self.action == "list":
            return ProfileListSerializer

        if self.action == "upload_profile_picture":
            return ProfileImageUpload

        return ProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        methods=["post"],
        detail=True,
    )
    def follow_or_unfollow(self, request, pk=None):
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

        serializer = self.get_serializer(data=following, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=True,
    )
    def followers(self, request, pk=None):
        """Return list of profiles that are following current profile"""
        profile = self.get_object()
        followers = profile.followers.all()

        serializer = self.get_serializer(data=followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=True,
    )
    def upload_profile_picture(self, request, pk=None):
        """Upload profile image of current profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(
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

    def get_queryset(self):
        queryset = self.queryset
        # If following_posts then return current user
        # followings posts
        current_profile = self.request.user.profile
        following_posts: bool = self.request.query_params.get("following_posts", None)

        if following_posts:
            queryset = current_profile.followings.all()

        return queryset

    def get_serializer_class(self):
        if self.action in ("profiles_liked", "profiles_disliked"):
            return ProfileListSerializer

        if self.action == "list":
            return PostListSerializer

        return PostSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)

        page = self.paginate_queryset(queryset)
        # Make annotation for already paginated queryset
        # instead of all objects in queryset
        # and order posts by number of likes and dislikes
        # and filter posts that are created within POST_CREATED_AT_DAYS_AGO
        days_ago = settings.POST_CREATED_AT_DAYS_AGO
        days_ago = timezone.now() - timezone.timedelta(days=days_ago)

        page = page.annotate(
            num_of_likes=Count(
                "postrate_set",
                filter=Q(postrate_set__like=True)
            ),
            num_of_dislikes=Count(
                "postrate_set",
                filter=Q(postrate_set__like=False)
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

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

