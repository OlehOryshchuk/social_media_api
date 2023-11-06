import os
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify


def custom_image_file_path(instance, filename):
    _, ext = os.path.splitext(filename)


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
