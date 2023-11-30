from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from taggit.models import Tag
from taggit.serializers import TagListSerializerField

from social_media.serializers import (
    PostListSerializer,
    TagListSerializer,
    TagSerializer
)

from social_media.models import (
    Post,
    PostRate,
    Profile
)

from .models_create_sample import (
    detail_url,
    create_number_of_posts,
    annotate_posts,
)

TAG_LIST = reverse("social_media:tag-list")


class UnauthenticatedTagsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="maintest@gmail.com", password="rvtrtyrpj", username="MainUseer"
        )

        create_number_of_posts(1, self.user.profile)
        self.post = Post.objects.all().first()

    def test_tags_list(self):
        tags = [Tag.objects.create(name=f"Tag{i}") for i in range(4)]

        res = self.client.get(TAG_LIST)

        serializer = TagListSerializer(
            tags, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data["results"])

    def test_tags_list_have_needed_fields(self):
        [Tag.objects.create(name=f"Tag{i}") for i in range(1)]

        res = self.client.get(TAG_LIST)
        tag = res.data["results"][0]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("name", tag)
        self.assertIn("tag_url", tag)

    def test_search_tag(self):
        searched_tag = Tag.objects.create(name="Searched")
        tags = [Tag.objects.create(name=f"Tag{i}") for i in range(4)]

        res = self.client.get(TAG_LIST, {"search": searched_tag.name})

        serializer = TagListSerializer(
            [searched_tag], many=True, context={"request": res.wsgi_request}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data["results"])

        serializer = TagListSerializer(
            tags, many=True, context={"request": res.wsgi_request}
        )
        self.assertNotEqual(serializer.data, res.data["results"])

    def get_tag_detail_endpoint_auth_required(self):
        tag = Tag.objects.create(name="Test_tag")
        res = self.client.get(detail_url("tag", tag.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def get_create_tag_auth_required(self):
        res = self.client.post(TAG_LIST, data={})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTagApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Main@gmail.com", password="rvtquen", username="MainUser"
        )
        self.client.force_authenticate(self.user)

        self.profile = self.user.profile
        create_number_of_posts(1, self.profile)
        self.post = Post.objects.first()

    def test_tag_list_available(self):
        res = self.client.get(TAG_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tag_detail_endpoint(self):
        tag1 = Tag.objects.create(name="Testtag1")

        for i in range(3):
            post = Post.objects.create(author=self.profile)
            post.tags.add(tag1)
            post.save()

        posts = annotate_posts(Post.objects.exclude(tags__id=tag1.id))
        tagged_posts = annotate_posts(Post.objects.filter(tags__id=tag1.id))

        res = self.client.get(detail_url("tag", tag1.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer1 = PostListSerializer(
            posts, many=True, context={"request": res.wsgi_request}
        )
        serializer2 = PostListSerializer(
            tagged_posts, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(res.data["results"], serializer2.data)
        self.assertNotEqual(res.data["results"], serializer1.data)

    def test_create_tag(self):
        data = {"name": "TestTagName"}

        res = self.client.post(TAG_LIST, data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        try:
            tag = Tag.objects.get(name=data["name"])
        except Post.DoestNotExist:
            raise AssertionError("Tag should exist after creation")
        serializer = TagSerializer(tag)

        self.assertEqual(res.data, serializer.data)
