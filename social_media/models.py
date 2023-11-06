import os
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify

from user.models import User


def get_file_new_name(instance) -> str:
    """Return filename base on instance"""
    if isinstance(instance, User):
        return f"{instance.username}_picture"
    return f"{instance.user.username}_post"


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
