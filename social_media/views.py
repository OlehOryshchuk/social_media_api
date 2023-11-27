from django.db.models import (
    Count,
    QuerySet,
)
from django.shortcuts import get_object_or_404

from rest_framework import status, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from taggit.models import Tag
from taggit.serializers import (
    TaggitSerializer
)

from .serializers import (
    TagListSerializer,
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

from .view_utils import (
    LikeDislikeObjectMixin,
    count_likes_dislikes,
    PaginateResponseMixin,
    schema_filter_by_username,
)

from .permissions import IsOwnerOrReadOnly


class ProfileViewSet(PaginateResponseMixin, viewsets.ModelViewSet):
    # TODO add filter by username
    serializer_class = ProfileSerializer
    queryset = Profile.objects.select_related("user")
    filter_backends = [SearchFilter]
    search_fields = ["user__username"]

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "retrieve":
            queryset = queryset.annotate(
                num_of_followers=Count("followers", distinct=True),
                num_of_followings=Count("followings", distinct=True),
                num_of_posts=Count("posts", distinct=True),
            )

        if self.action == "followers":
            pass

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProfileDetailSerializer

        if self.action in ["list", "followings", "followers"]:
            return ProfileListSerializer

        if self.action == "upload_profile_picture":
            return ProfileImageUpload

        return ProfileSerializer

    def get_permissions(self):
        if self.action in [
            "follow_or_unfollow",
            "followings",
            "followers",
            "upload_profile_picture"
        ]:
            self.permission_classes = [IsAuthenticated]

        elif self.action in ["update", "partial_update", "destroy", "create"]:
            self.permission_classes = [IsOwnerOrReadOnly]

        return super().get_permissions()

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

    @schema_filter_by_username
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @schema_filter_by_username
    @action(methods=["get"], detail=True)
    def followings(self, request, pk=None):
        """Return list of profiles current profile is following"""
        profile = self.get_object()
        following = profile.followings.select_related("user")
        filter_que = self.filter_queryset(following)

        return self.custom_paginate_queryset(filter_que)

    @schema_filter_by_username
    @action(methods=["get"], detail=True,)
    def followers(self, request, pk=None):
        """Return list of profiles that are following current profile"""
        profile = self.get_object()
        followers = profile.followers.select_related("user")
        filter_que = self.filter_queryset(followers)

        return self.custom_paginate_queryset(filter_que)

    @action(methods=["post"], detail=True,)
    def upload_profile_picture(self, request, pk=None):
        """Upload profile image on current profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(
    PaginateResponseMixin,
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

    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        queryset = self.queryset
        following_posts: bool = self.request.query_params.get("following_posts", None)

        if following_posts:
            current_profile = self.request.user.profile
            queryset = Post.objects.filter(author__followers=current_profile)

        if self.action == "list":
            queryset = self.get_serializer().setup_eager_loading(queryset)

        queryset = count_likes_dislikes(queryset, "postrate")

        # Count the number of comments for each post
        queryset = queryset.annotate(num_of_comments=Count("comments", distinct=True))

        queryset = queryset.order_by("-created_at", "num_of_comments")

        return queryset

    def get_serializer_class(self):
        if self.action in [
                "profile_posts",
                "list",
                "post_liked",
                "post_disliked",
        ]:
            return PostListSerializer

        if self.action in [
            "profiles_liked",
            "profiles_disliked"
        ]:
            return ProfileListSerializer

        return PostSerializer

    def get_permissions(self):
        if self.action in [
            "profiles_liked",
            "profiles_disliked",
            "dislike_remove_dislike",
            "like_unlike",
            "post_liked",
            "post_disliked"
        ]:
            self.permission_classes = [IsAuthenticated]

        elif self.action in ["update", "partial_update", "destroy", "create"]:
            self.permission_classes = [IsOwnerOrReadOnly]

        return super().get_permissions()

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
        profile_ids = post.postrate_set.filter(like=like_value).values_list("profile")
        data = Profile.objects.filter(id__in=profile_ids).select_related("user")

        return self.custom_paginate_queryset(data)

    def _get_posts_current_profile_liked_disliked(self, request, like_value: bool):
        profile = request.user.profile
        posts_ids = profile.postrate_set.filter(like=like_value).values_list("post")
        data = Post.objects.filter(id__in=posts_ids)

        improve_queries = self.get_serializer().setup_eager_loading(data)

        annotate = count_likes_dislikes(improve_queries, "postrate").annotate(
            num_of_comments=Count("comments", distinct=True)
        ).order_by("-num_of_comments")

        return self.custom_paginate_queryset(annotate)

    @action(methods=["get"], detail=True,)
    def profiles_liked(self, request, pk):
        """Return profiles who liked post"""
        return self._get_post_profiles_who_likes_or_dislikes(request, True)

    @action(methods=["get"], detail=True, url_name="profile-disliked")
    def profiles_disliked(self, request, pk):
        """Return profiles who disliked post"""
        return self._get_post_profiles_who_likes_or_dislikes(request, False)

    @action(methods=["get"], detail=False, url_name="liked")
    def post_liked(self, request):
        """Return posts current profile liked"""
        return self._get_posts_current_profile_liked_disliked(request, True)

    @action(methods=["get"], detail=False, url_name="disliked")
    def post_disliked(self, request):
        """Return posts current profile disliked"""
        return self._get_posts_current_profile_liked_disliked(request, False)

    @action(
        methods=["get"],
        detail=True,
        url_path="profile",
        url_name="profile",
    )
    def profile_posts(self, request, pk):
        """Accept profile pk and return profile posts"""
        profile = get_object_or_404(Profile, id=pk)
        data = Post.objects.filter(author=profile)

        improve_queries = self.get_serializer().setup_eager_loading(data)

        annotate = count_likes_dislikes(improve_queries, "postrate").annotate(
            num_of_comments=Count("comments", distinct=True)
        ).order_by("-num_of_comments")

        return self.custom_paginate_queryset(annotate)


class CommentViewSet(
    PaginateResponseMixin,
    LikeDislikeObjectMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """List comments under post pk, Detail - return replies under comment
    Create/Update/Delete comment"""

    serializer_class = CommentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at"]
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
        """Return Post comments not replies"""
        queryset = Comment.objects.all().filter(
            post=self.get_post(),
            reply_to_comment__isnull=True
        )
        return self.annotate_queryset(queryset)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CommentListSerializer

        return CommentSerializer

    def get_permissions(self):
        if self.action in [
            "dislike_remove_dislike",
            "like_unlike",
            "list",
            "retrieve",
        ]:
            self.permission_classes = [IsAuthenticated]

        elif self.action in ["update", "partial_update", "destroy", "create"]:
            self.permission_classes = [IsOwnerOrReadOnly]

        return super().get_permissions()

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
        improve_queries = self.get_serializer().setup_eager_loading(comments)
        queryset = self.filter_queryset(improve_queries)

        return self.custom_paginate_queryset(queryset)

    def retrieve(self, request, post_pk: int, pk: int):
        """GET comment replies"""
        replies = self.get_comment().replies
        improve_queries = self.get_serializer().setup_eager_loading(replies)
        annotate = count_likes_dislikes(improve_queries, "commentrate")
        queryset = self.filter_queryset(annotate)

        return self.custom_paginate_queryset(queryset)


class TagViewSet(
    PaginateResponseMixin,
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

    def get_permissions(self):
        if self.action in [
            "retrieve",
            "create"
        ]:
            self.permission_classes = [IsAuthenticated]

        return super().get_permissions()

    def retrieve(self, request, pk):
        """Return posts under tag pk"""
        tag = get_object_or_404(Tag, id=pk)
        data = Post.objects.filter(tags__id=tag.id)

        annotate = count_likes_dislikes(data, "postrate").annotate(
            num_of_comments=Count("comments")
        ).order_by("num_of_comments")

        improve_queries = self.get_serializer().setup_eager_loading(annotate)

        return self.custom_paginate_queryset(improve_queries)
