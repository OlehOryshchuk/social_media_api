from django.contrib.auth.models import Group
from django.contrib import admin
from .models import Profile, Post

admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ["user__username", "user__email"]
    list_display = [
        "user",
        "profile_picture",
        "bio"
    ]
