from django.urls import path

from .views import CreateUserView, ManagerUserView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("me/", ManagerUserView.as_view(), name="me"),
]

app_name = "user"
