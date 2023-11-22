from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from .views import UserViewSet
router = DefaultRouter()

router.register("user", UserViewSet)

password_reset_complete = reverse_lazy("user:user-me")

urlpatterns = [
    path("", include(router.urls)),
    path("user/password-reset-confirm/<str:uidb64>/<str:token>/",
         auth_views.PasswordResetConfirmView.as_view(
            success_url=password_reset_complete
         ),
         name='password_reset_confirm'
         ),
    path("user/password-reset-complete/",
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'
         ),
    path("auth/", include("djoser.urls.authtoken")),
]

app_name = "user"
