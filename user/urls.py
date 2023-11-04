from django.urls import path
from knox.views import (
    LoginView,
    LogoutView,
    LogoutAllView,
)

from .views import CreateUserView, ManagerUserView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("me/", ManagerUserView.as_view(), name="me"),

    # path("login/", LogInUser.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("logout_all", LogoutAllView.as_view(), name="logout_all"),
]

app_name = "user"
