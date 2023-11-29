from django.db.models import Count
from django.urls import reverse
from django.contrib.auth import get_user_model

from social_media.models import Profile, Post
from social_media.view_utils import count_likes_dislikes


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


def annotate_posts(posts):
    return count_likes_dislikes(posts, "postrate").annotate(
        num_of_comments=Count("comments", distinct=True)
    ).order_by("-num_of_comments", "-created_at")


def create_number_of_posts(number: int, profile: Profile = None):
    if profile:
        # if profile is provided then used it
        pass
    else:
        # else there is no profile provided, create
        user = get_user_model().objects.create_user(
            email="number_of_posts@gmail.com", password="rvrtrt", username="Count"
        )
        profile = user.profile

    for i in range(number):
        Post.objects.create(
            author=profile
        )

