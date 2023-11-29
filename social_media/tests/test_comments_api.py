from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from social_media.serializers import (
    CommentSerializer,
    CommentListSerializer,
)
from social_media.models import (
    Post,
    Comment,
    CommentRate
)
from social_media.view_utils import count_likes_dislikes

from .models_create_sample import (
    create_number_of_posts,
    create_number_of_comments,
    annotate_comments,
    annotate_posts,
)


def comment_manager_url(comment_id):
    return reverse("social_media:comment-manager", args=[comment_id])


def post_comment_list(post_id):
    return reverse("social_media:post-comments", args=[post_id])


def comment_replies_list(comment_id):
    return reverse("social_media:comment-replies", args=[comment_id])


def dislike_remove_disliked_url(comment_id):
    return reverse("social_media:comment-dislike", args=[comment_id])


def like_unliked_url(comment_id):
    return reverse("social_media:comment-like", args=[comment_id])


class UnauthenticatedCommentApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="maintest@gmail.com", password="rvtrtyrpj", username="MainUseer"
        )

        self.profile = self.user.profile

        create_number_of_posts(1, self.user.profile)
        self.post = Post.objects.all().first()

        self.comment = Comment.objects.create(
            author=self.profile, post=self.post
        )

    def test_get_post_comments_auth_required(self):
        res = self.client.get(post_comment_list(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_comment_replies_auth_required(self):
        res = self.client.get(comment_replies_list(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_comment_auth_required(self):
        res = self.client.post(like_unliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dislike_comment_auth_required(self):
        res = self.client.post(dislike_remove_disliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_auth_required(self):
        res = self.client.post(post_comment_list(self.post.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_comment_auth_required(self):
        res = self.client.put(comment_manager_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.patch(comment_manager_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_post_auth_required(self):
        res = self.client.delete(comment_manager_url(self.comment.id))
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

        self.comment = Comment.objects.create(
            author=self.profile, post=self.post
        )

    def test_get_post_comments(self):
        create_number_of_comments(3, self.post)

        res = self.client.get(post_comment_list(self.post.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        comments = Comment.objects.filter(
            post=self.post,
            reply_to_comment__isnull=True
        )
        annotated = annotate_comments(comments)
        serializer = CommentListSerializer(
            annotated, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(serializer.data, res.data["results"])

    def test_get_comment_replies(self):
        create_number_of_comments(3, self.post, profile=self.profile, reply_to_comment=self.comment)

        res = self.client.get(comment_replies_list(self.comment.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        replies = self.comment.replies.all()
        annotated = count_likes_dislikes(replies, "commentrate")
        serializer = CommentListSerializer(
            annotated, many=True, context={"request": res.wsgi_request}
        )

        self.assertEqual(serializer.data, res.data["results"])

    def test_like_comment(self):
        res = self.client.post(like_unliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_liked = self.comment.commentrate_set.filter(like=True)
        self.assertIn(self.profile.id, profiles_liked.values_list("profile", flat=True))

    def test_unlike_comment(self):
        CommentRate.objects.create(
            like=True, comment=self.comment, profile=self.profile
        )

        res = self.client.post(like_unliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_liked = self.comment.commentrate_set.filter(like=True)
        self.assertNotIn(self.profile.id, profiles_liked.values_list("profile", flat=True))

    def test_dislike_comment(self):
        res = self.client.post(dislike_remove_disliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_disliked = self.comment.commentrate_set.filter(like=False)
        self.assertIn(self.profile.id, profiles_disliked.values_list("profile", flat=True))

    def test_dislike_remove_dislike_comment(self):
        CommentRate.objects.create(
            like=False, comment=self.comment, profile=self.profile
        )

        res = self.client.post(dislike_remove_disliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profiles_disliked = self.comment.commentrate_set.filter(like=False)
        self.assertNotIn(self.profile.id, profiles_disliked.values_list("profile", flat=True))

    def test_like_comment_profile_required(self):
        self.profile.delete()
        self.user.refresh_from_db()

        res = self.client.post(like_unliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_dislike_comment_profile_required(self):
        self.profile.delete()
        self.user.refresh_from_db()

        res = self.client.post(dislike_remove_disliked_url(self.comment.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
