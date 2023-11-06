from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from social_media.models import Profile

user = settings.AUTH_USER_MODEL


@receiver(post_save, sender=user)
def create_profile(sender: post_save, instance: user, created: bool, **kwargs):
    """When user is save to DB we will create user profile"""
    if created and not instance.is_staff:
        Profile.objects.create(user=instance)
