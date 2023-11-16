from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, PostViewSet, CommentViewSet, TagViewSet

app_name = "social_media"

router = DefaultRouter()
router.register("profiles", ProfileViewSet)
router.register("posts", PostViewSet)
router.register("tags", TagViewSet)

# create, delete, update endpoints
cr_up_de = {
    "delete": "destroy",
    "patch": "update",
}

urlpatterns = [
    path("", include(router.urls)),
    path(
        "post/<int:post_pk>/comments/",
        CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="post-comments",
    ),
    path(
        "post/<int:post_pk>/comments/<int:pk>/",
        CommentViewSet.as_view(
            {"get": "detail", "post": "create"}
        ),
        name="comment-replies",
    ),
    path(
        "post/<int:post_pk>/comments/<int:pk>/",
        CommentViewSet.as_view(
            {**cr_up_de}
        ),
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
