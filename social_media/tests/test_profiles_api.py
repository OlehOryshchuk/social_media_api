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

    def test_follow_unfollow_profile_auth_required(self):
        res = self.client.post(upload_profile_picture_url(self.user.profile.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_auth_required(self):
        res = self.client.put(detail_url("profile", self.user.profile.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_profile_auth_required(self):
        res = self.client.patch(detail_url("profile", self.user.profile.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_profile_auth_required(self):
        res = self.client.delete(detail_url("profile", self.user.profile.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedProfileApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Main@gmail.com", password="rvtquen", username="MainUser"
        )
        self.client.force_authenticate(self.user)

        self.profile = self.user.profile

    def test_list_available(self):
        res = self.client.get(PROFILE_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_detail_available(self):
        res = self.client.get(detail_url("profile", self.profile.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_profile_followings_available(self):
        for i in range(3):
            new_user = get_user_model().objects.create_user(
                email=f"test{i}@gmail.com",
                password="rctvrtry",
                username=f"{i}User"
            )
            self.profile.followings.add(new_user.profile)
            self.profile.save()

        res = self.client.get(followings_url(self.profile.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        followings = self.profile.followings.all()
        serializer = ProfileListSerializer(
            followings, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.data["results"], serializer.data)

    def test_get_profile_followers_available(self):
        for i in range(3):
            new_user = get_user_model().objects.create_user(
                email=f"test{i}@gmail.com",
                password="rctvrtry",
                username=f"{i}User"
            )
            self.profile.followers.add(new_user.profile)
            self.profile.save()

        res = self.client.get(followers_url(self.profile.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        followings = self.profile.followers.all()
        serializer = ProfileListSerializer(
            followings, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.data["results"], serializer.data)

    def test_follow_profile(self):
        test_user = get_user_model().objects.create_user(
            email="testuser@gmail.com", password="rvtrsgh", username="testUser"
        )
        test_profile = test_user.profile

        res = self.client.post(follow_unfollow_url(test_profile.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(test_profile, self.profile.followings.all())

    def test_unfollow_profile(self):
        test_user = get_user_model().objects.create_user(
            email="testuser@gmail.com", password="rvtrsgh", username="testUser"
        )
        test_profile = test_user.profile
        self.profile.followings.add(test_profile)
        self.profile.save()

        res = self.client.post(follow_unfollow_url(test_profile.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(test_profile, self.profile.followings.all())
