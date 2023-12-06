from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, PostViewSet, CommentViewSet, TagViewSet

app_name = "social_media"

router = DefaultRouter()
router.register("profiles", ProfileViewSet)
router.register("posts", PostViewSet)
router.register("tags", TagViewSet)

# update, delete, retrieve endpoints
up_de_rt = {
    "get": "retrieve",
    "delete": "destroy",
    "patch": "update",
    "put": "update"
}

urlpatterns = [
    path("", include(router.urls)),
    path(
        "post/<int:post_pk>/comments/",
        CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="post-comments",
    ),
    path(
        "post/comments/<int:pk>/replies/",
        CommentViewSet.as_view({"get": "replies"}),
        name="comment-replies",
    ),
    path(
        "post/comments/<int:pk>/",
        CommentViewSet.as_view({**up_de_rt}),
        name="comment-manager",
    ),
    path(
        "post/comments/<int:pk>/like",
        CommentViewSet.as_view({"post": "like_unlike"}),
        name="comment-like",
    ),
    path(
        "post/comments/<int:pk>/dislike",
        CommentViewSet.as_view({"post": "dislike_remove_dislike"}),
        name="comment-dislike",
    ),
]
