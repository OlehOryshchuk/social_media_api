from django.dispatch import receiver
from django.db.models.signals import post_save

from social_media.models import Profile
from .models import User


@receiver(post_save, sender=User)
def create_profile(
        sender: post_save,
        instance: User,
        created: bool,
        **kwargs
):
    """When user is save to DB we will create user profile"""
    if created and not instance.is_staff:
        Profile.objects.create(user=instance)
