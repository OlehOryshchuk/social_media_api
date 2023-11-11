import os
import uuid

from django.db import models
from django.conf import settings
from django.utils.text import slugify

from taggit.managers import TaggableManager


def get_file_new_name(instance) -> str:
    """Return filename base on instance"""
    if getattr(instance, "username"):
        return f"{instance.user.username}"
    return f"{instance.author.user.username}_post"


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
        symmetrical=False,
        blank=True
    )
    profile_picture = models.ImageField(
        null=True,
        blank=True,
        upload_to=custom_image_file_path
    )
    bio = models.TextField(max_length=1000, blank=True)

    def __str__(self) -> str:
        return self.user


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
        through_fields=("post", "profile"),
        blank=True,
    )
    comments = models.ManyToManyField(
        Profile,
        related_name="comments",
        through="Comment",
        through_fields=("post", "author"),
        blank=True
    )
    tags = TaggableManager(
        blank=True,
        related_name="posts"
    )

    class Meta:
        indexes = [
            models.Index(fields=["created_at"])
        ]

    def __str__(self) -> str:
        return f"{self.author} - {self.created_at}"


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
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to_comment = models.ForeignKey(
        "self",
        related_name="replies",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    likes = models.ManyToManyField(
        Profile,
        related_name="liked_comments",
        through="CommentRate",
        through_fields=("comment", "profile")
    )

    def __str__(self) -> str:
        return f"{self.author} {self.post}"


class CommentRate(models.Model):
    like = models.BooleanField()
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.profile} {self.comment}"
