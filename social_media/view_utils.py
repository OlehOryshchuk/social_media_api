from abc import ABC, abstractmethod

from django.db.models import (
    Q,
    Count,
    QuerySet,
)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action


def count_likes_dislikes(queryset: QuerySet, rate_model: str) -> QuerySet:
    """Count number of likes and dislikes"""
    if type(rate_model) != str:
        raise ValueError("rate_model have to be string")
    rate_model = rate_model.lower()

    queryset = queryset.annotate(
        num_of_likes=Count(rate_model, filter=Q(**{f"{rate_model}__like": True})),
        num_of_dislikes=Count(rate_model, filter=Q(**{f"{rate_model}__like": False}))
    ).order_by(
        "-num_of_likes",
        "num_of_dislikes",
    )

    return queryset


class LikeDislikeObjectMixin(ABC):
    @abstractmethod
    def _like_dislike_or_remove(self, request, like_value: bool):
        pass

    @action(methods=["post"], detail=True, url_path="like", url_name="like")
    def like_unlike(self, request, pk):
        """Like or unlike post"""
        self._like_dislike_or_remove(request, True)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path="dislike", url_name="dislike")
    def dislike_remove_dislike(self, request, pk):
        """DisLike post or remove dislike"""
        self._like_dislike_or_remove(request, False)
        return Response(status=status.HTTP_200_OK)

