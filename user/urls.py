from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

router = DefaultRouter()
router.register("user", UserViewSet)

login = reverse_lazy("user:login")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "user/password_reset_confirm/<str:uidb64>/<str:token>/",
        auth_views.PasswordResetConfirmView.as_view(
            success_url=login
        ),
        name="password_reset_confirm",
    ),
    path("auth/", include("djoser.urls.authtoken")),
]

app_name = "user"
