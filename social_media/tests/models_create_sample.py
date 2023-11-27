from django.urls import reverse
from django.contrib.auth import get_user_model


def detail_url(view_name: str, instance_id: int):
    return reverse(f"social_media:{view_name}-detail", args=[instance_id])


def create_number_users(number: int):
    for i in range(number + 1):
        get_user_model().objects.create_user(
            email=f"testuser{i}@gmail.com",
            password="rvtrtyrpj",
            username=f"User{i}"
        )


def annotate_profile(profile):
    profile.num_of_followers = profile.followers.count()
    profile.num_of_followings = profile.followings.count()
    profile.num_of_posts = profile.posts.count()

    return profile
