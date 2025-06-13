from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from news.models import Comment
from summarizer.models import NewsSummary
from news.serializers.serializers import CommentSerializer
from django.shortcuts import get_object_or_404
from news.permissions import IsOwnerOrAdminOrReadOnly
import logging

from news.news.news_controller import news_controller

logger = logging.getLogger(__name__)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        summary_id = self.kwargs.get('summary_id')

        return news_controller.get_comments_interface(summary_id)

    def perform_create(self, serializer):
        summary_id = self.kwargs.get('summary_id')
        try:
            summary = get_object_or_404(NewsSummary, id=summary_id)

            comment_instance = serializer.save(
                user_id=self.request.user.id,
                article_id=summary.article_id
            )

            # Gọi interface từ news_controller để cập nhật stats
            if comment_instance and summary.article_id:
                news_controller.handle_new_comment_stats_interface(
                    summary.article_id)

        except NewsSummary.DoesNotExist:  # Bắt lỗi nếu get_object_or_404 thất bại
            raise NotFound(
                detail=f"Không tìm thấy tóm tắt với ID: {summary_id} khi tạo bình luận.",
                code="summary_not_found_on_create")
        except Exception as e:
            logger.error(
                f"Lỗi khi tạo bình luận cho summary {summary_id}: {e}",
                exc_info=True)
            raise


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrAdminOrReadOnly]
    lookup_field = 'id'

    def perform_destroy(self, instance):
        article_id = instance.article_id
        super().perform_destroy(instance)
        if article_id:
            news_controller.handle_deleted_comment_stats_interface(article_id)
