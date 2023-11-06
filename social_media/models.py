import os
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify

from taggit.managers import TaggableManager

from user.models import User


def get_file_new_name(instance) -> str:
    """Return filename base on instance"""
    if isinstance(instance, User):
        return f"{instance.username}_picture"
    return f"{instance.author.username}_post"


def custom_image_file_path(instance, filename):
    _, ext = os.path.splitext(filename)
    filename = get_file_new_name(instance)
    return f"{slugify(filename)}_{uuid.uuid4()}{ext}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    followings = models.ManyToManyField(
        "self",
        related_name="followers",
        symmetrical=True,
        blank=True
    )
    profile_picture = models.ImageField(
        null=True,
        blank=True,
        upload_to=custom_image_file_path
    )
    bio = models.TextField(max_length=1000, blank=True)

    def __str__(self) -> str:
        return self.user.username

    def get_followers(self):
        """Return profiles that are following current profile"""
        return self.followers.all()

    def get_followings(self):
        """Return profiles that current profile is following """
        return self.followings.all()


class Post(models.Model):
    author = models.ForeignKey(
        Profile,
        related_name="posts",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to=custom_image_file_path,
        blank=True
    )
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(
        Profile,
        related_name="liked_posts",
        through="PostRate",
        blank=True,
    )
    comments = models.ManyToManyField(
        Profile,
        related_name="comments",
        through="Comment",
        through_fields=("author", "post"),
        blank=True
    )
    tags = TaggableManager(
        blank=True,
        related_name="posts"
    )


class PostRate(models.Model):
    like = models.BooleanField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.profile} {self.post}"


class Comment(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    reply_to_comment = models.ForeignKey(
        "self",
        related_name="replies",
        on_delete=models.SET_NULL
    )
    likes = models.ManyToManyField(
        Profile,
        related_name="liked_comments",
        through="CommentRate",
        through_fields=("profile", "comment")
    )

    def __str__(self) -> str:
        return f"{self.author} {self.post}"


class CommentRate(models.Model):
    like = models.BooleanField()
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.profile} {self.comment}"
