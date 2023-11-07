from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.utils.translation import gettext as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with given email and password."""
        if not email:
            raise ValueError("The email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with email and password"""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a Superuser with password and email"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(_("Email address"), unique=True)

    # Specifies email as the unique identifier for a user.
    # and create superuser through email and password
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
