import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from social_media.serializers import (
    PostSerializer,
    PostListSerializer
)

from social_media.models import (
    Post,
    PostRate
)

from .models_create_sample import (
    detail_url,
    create_number_of_posts,
    annotate_posts,
)

POST_LIST = reverse("social_media:post-list")


def dislike_remove_disliked_url(post_id):
    return reverse("social_media:post-dislike", args=[post_id])


def like_unliked_url(post_id):
    return reverse("social_media:post-like", args=[post_id])


def posts_liked_url():
    return reverse("social_media:post-liked")


def posts_disliked_url():
    return reverse("social_media:post-disliked")


def profiles_liked_url(post_id):
    return reverse("social_media:post-profiles-liked", args=[post_id])


def profiles_disliked_url(post_id):
    return reverse("social_media:post-profiles-disliked", args=[post_id])


class UnauthenticatedProfileApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="maintest@gmail.com", password="rvtrtyrpj", username="MainUseer"
        )

        create_number_of_posts(1, self.user.profile)
        self.post = Post.objects.all().first()

    def test_list_allow_anonymous_user(self):
        create_number_of_posts(3)

        res = self.client.get(POST_LIST)

        posts = Post.objects.all()
        posts = annotate_posts(posts)

        serializer = PostListSerializer(
            posts, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_response_has_needed_fields(self):
        create_number_of_posts(2)

        res = self.client.get(POST_LIST)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        first_post = res.data["results"][0]

        self.assertIn("author", first_post)
        self.assertIn("comments_url", first_post)
        self.assertIn("like_url", first_post)
        self.assertIn("dislike_url", first_post)
        self.assertIn("num_of_comments", first_post)
        self.assertIn("tags", first_post)

    def test_like_post_auth_required(self):
        res = self.client.post(like_unliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dislike_post_auth_required(self):
        res = self.client.post(dislike_remove_disliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profiles_that_liked_post_auth_required(self):
        res = self.client.get(profiles_liked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profiles_that_disliked_post_auth_required(self):
        res = self.client.get(profiles_disliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_posts_current_profile_liked_auth_required(self):
        res = self.client.get(posts_liked_url())
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_posts_current_profile_disliked_auth_required(self):
        res = self.client.get(posts_disliked_url())
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_auth_required(self):
        res = self.client.post(POST_LIST)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_post_auth_required(self):
        res = self.client.put(detail_url("post", self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.patch(detail_url("post", self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_post_auth_required(self):
        res = self.client.delete(detail_url("post", self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

#
# class AuthenticatedPostApiTests(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.user = get_user_model().objects.create_user(
#             email="Main@gmail.com", password="rvtquen", username="MainUser"
#         )
#         self.client.force_authenticate(self.user)
#
#         self.profile = self.user.profile
#         create_number_of_posts(1, self.profile)
#         self.post = Post.objects.first()
