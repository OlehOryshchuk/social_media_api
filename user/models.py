from typing import Any

from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.utils.translation import gettext as _


class UserManager(BaseUserManager):
    """Define a model manager for a User model with no username field"""

    use_in_migrations = True

    def _create_user(self, email: str, password: Any, **extra_kwargs):
        """Create and save a User with password and email field."""
        if not email:
            raise ValueError("The email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_kwargs)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email: str, password: Any, **extra_kwargs):
        """Create and save a regular User with password and email"""
        extra_kwargs.setdefault("is_staff", False)
        extra_kwargs.setdefault("is_superuser", False)

        return self._create_user(email, password, **extra_kwargs)

    def create_superuser(self, email: str, password: Any, **extra_kwargs):
        """Create and save a Superuser with password and email"""
        extra_kwargs.update({
            "is_staff": True,
            "is_superuser": True,
        })

        return self._create_user(email, password, **extra_kwargs)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("Email address"), unique=True)

    # Specifies email as the unique identifier for a user.
    # and create superuser through email and password
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
