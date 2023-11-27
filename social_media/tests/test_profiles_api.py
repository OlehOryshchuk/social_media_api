import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from social_media.serializers import (
    ProfileSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileImageUpload
)

from social_media.models import (
    Profile
)

from .models_create_sample import (
    detail_url,
    create_number_users,
    annotate_profile,
)

PROFILE_LIST = reverse("social_media:profile-list")


def followings_url(profile_id: int):
    """Return url to see profile followings"""
    return reverse("social_media:profile-followings", args=[profile_id])


def followers_url(profile_id: int):
    """Return url to see profile followings"""
    return reverse("social_media:profile-followers", args=[profile_id])


def follow_unfollow_url(profile_id: int):
    """Return url to see profile followings"""
    return reverse("social_media:profile-follow-unfollow", args=[profile_id])


def upload_profile_picture_url(profile_id: int):
    return reverse("social_media:profile-upload-profile-picture", args=[profile_id])


class UnauthenticatedProfileApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="maintest@gmail.com", password="rvtrtyrpj", username="MainUseer"
        )

    def test_list_allow_anonymous_user(self):
        create_number_users(3)

        res = self.client.get(PROFILE_LIST)

        profiles = Profile.objects.all()
        serializer = ProfileListSerializer(
            profiles, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_search_list_by_username(self):
        searched_user = get_user_model().objects.create_user(
            email="searchead@gmail.com", password="rvtrtyrpj", username="SearchedUseer"
        )
        create_number_users(3)

        res = self.client.get(PROFILE_LIST, {"search": searched_user.username})

        searched_user = Profile.objects.filter(user__username=searched_user.username)
        serializer = ProfileListSerializer(
            searched_user, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_response_has_needed_fields(self):
        res = self.client.get(PROFILE_LIST)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        first_profile = res.data["results"][0]

        self.assertIn("username", first_profile)
        self.assertIn("profile_picture", first_profile)
        self.assertIn("profile_url", first_profile)

    def test_detail_allow_anonymous_user(self):
        res = self.client.get(detail_url("profile", self.user.id))

        profile = annotate_profile(self.user.profile)
        serializer = ProfileDetailSerializer(
            profile, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_detail_response_has_needed_fields(self):
        res = self.client.get(detail_url("profile", self.user.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn("is_following", res.data)
        self.assertIn("followers", res.data)
        self.assertIn("followings", res.data)
        self.assertIn("num_of_followers", res.data)
        self.assertIn("num_of_followings", res.data)
        self.assertIn("num_of_posts", res.data)
        self.assertIn("posts", res.data)

    def test_create_profile_auth_required(self):
        res = self.client.post(PROFILE_LIST)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_followings_auth_required(self):
        res = self.client.get(followings_url(self.user.profile))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_followers_auth_required(self):
        res = self.client.get(followers_url(self.user.profile))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_unfollow_profile_forbidden(self):
        res = self.client.get(upload_profile_picture_url(self.user.profile))
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)



