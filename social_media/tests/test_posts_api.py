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
    PostListSerializer,
    ProfileListSerializer,
)

from social_media.models import Post, PostRate, Profile

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


class UnauthenticatedPostApiTests(TestCase):
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


class AuthenticatedPostApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Main@gmail.com", password="rvtquen", username="MainUser"
        )
        self.client.force_authenticate(self.user)

        self.profile = self.user.profile
        create_number_of_posts(1, self.profile)
        self.post = Post.objects.first()

    def test_list_available(self):
        res = self.client.get(POST_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_like_post(self):
        res = self.client.post(like_unliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_liked = self.post.postrate_set.filter(like=True)
        self.assertIn(self.profile.id, profiles_liked.values_list("profile", flat=True))

    def test_unlike_post(self):
        PostRate.objects.create(like=True, profile=self.profile, post=self.post)

        res = self.client.post(like_unliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_liked = self.post.postrate_set.filter(like=True)
        self.assertNotIn(
            self.profile.id, profiles_liked.values_list("profile", flat=True)
        )

    def test_dislike_post(self):
        res = self.client.post(dislike_remove_disliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_disliked = self.post.postrate_set.filter(like=False)
        self.assertIn(
            self.profile.id, profiles_disliked.values_list("profile", flat=True)
        )

    def test_dislike_remove_dislike_post(self):
        PostRate.objects.create(like=False, profile=self.profile, post=self.post)

        res = self.client.post(dislike_remove_disliked_url(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_disliked = self.post.postrate_set.filter(like=False)
        self.assertNotIn(
            self.profile.id, profiles_disliked.values_list("profile", flat=True)
        )

    def test_profiles_liked_posts(self):
        profile2 = (
            get_user_model()
            .objects.create_user(
                username="TestDisliked", password="ectevy", email="disliked@gmail.com"
            )
            .profile
        )

        PostRate.objects.create(like=True, profile=self.profile, post=self.post)
        PostRate.objects.create(like=False, profile=profile2, post=self.post)

        res = self.client.get(profiles_liked_url(self.post.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_liked = self.post.postrate_set.filter(like=True).values_list(
            "profile", flat=True
        )
        profiles = Profile.objects.filter(id__in=profiles_liked)
        serializer = ProfileListSerializer(
            profiles, many=True, context={"request": res.wsgi_request}
        )
        self.assertEqual(serializer.data, res.data["results"])
        self.assertNotIn(profile2, profiles_liked)

    def test_profiles_disliked_posts(self):
        profile2 = (
            get_user_model()
            .objects.create_user(
                username="TestDisliked", password="ectevy", email="disliked@gmail.com"
            )
            .profile
        )
        PostRate.objects.create(like=True, profile=profile2, post=self.post)
        PostRate.objects.create(like=False, profile=self.profile, post=self.post)

        res = self.client.get(profiles_disliked_url(self.post.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_disliked = self.post.postrate_set.filter(like=False).values_list(
            "profile", flat=True
        )
        profiles = Profile.objects.filter(id__in=profiles_disliked)
        serializer = ProfileListSerializer(
            profiles, many=True, context={"request": res.wsgi_request}
        )
        self.assertEqual(serializer.data, res.data["results"])
        self.assertNotIn(profile2, profiles_disliked)

    def test_current_profile_liked_posts(self):
        post2 = create_number_of_posts(1, profile=self.profile)[0]
        PostRate.objects.create(like=True, profile=self.profile, post=self.post)
        PostRate.objects.create(like=False, profile=self.profile, post=post2)

        res = self.client.get(posts_liked_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        posts_liked = self.profile.postrate_set.filter(like=True).values_list(
            "post", flat=True
        )
        posts = Post.objects.filter(id__in=posts_liked)
        annotated = annotate_posts(posts)

        serializer = PostListSerializer(
            annotated, many=True, context={"request": res.wsgi_request}
        )
        self.assertEqual(serializer.data, res.data["results"])
        self.assertNotIn(post2, posts_liked)

    def test_current_profile_disliked_posts(self):
        post2 = create_number_of_posts(1, profile=self.profile)[0]
        PostRate.objects.create(like=True, profile=self.profile, post=post2)
        PostRate.objects.create(like=False, profile=self.profile, post=self.post)

        res = self.client.get(posts_disliked_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        posts_disliked = self.profile.postrate_set.filter(like=False).values_list(
            "post", flat=True
        )
        posts = Post.objects.filter(id__in=posts_disliked)
        annotated = annotate_posts(posts)

        serializer = PostListSerializer(
            annotated, many=True, context={"request": res.wsgi_request}
        )
        self.assertEqual(serializer.data, res.data["results"])
        self.assertNotIn(post2, posts_disliked)

    def test_create_post_profile_required(self):
        self.user.profile.delete()
        self.user.refresh_from_db()

        res = self.client.post(POST_LIST, data={})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_valid_post(self):
        data = {"content": "Yeah this is test"}
        res = self.client.post(POST_LIST, data=data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        try:
            post = Post.objects.get(content=data["content"])
        except Post.DoestNotExist:
            raise AssertionError("Post should exist after creation")

        serializer = PostSerializer(post)
        self.assertEqual(serializer.data, res.data)

    def test_update_post(self):
        data_put = {"content": "Yeah this is test"}
        data_patch = {"tags": ["test"]}
        res = self.client.put(detail_url("post", self.post.id), data=data_put)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        serializer = PostSerializer(self.post)
        self.assertEqual(serializer.data, res.data)

        res = self.client.patch(detail_url("post", self.post.id), data=data_patch)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        serializer = PostSerializer(self.post)
        self.assertEqual(serializer.data, res.data)
