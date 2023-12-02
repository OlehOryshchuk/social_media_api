from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.utils.translation import gettext as _


class User(AbstractUser):
    email = models.EmailField(_("Email address"), unique=True)

    # Specifies email as the unique identifier for a user.
    # and create superuser through email and password
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.username
