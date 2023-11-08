from django.db.models import Count, F, QuerySet

from rest_framework import status, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from taggit.models import Tag

from .serializers import (
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,

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
    def followings(self, request, pk=None):
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
