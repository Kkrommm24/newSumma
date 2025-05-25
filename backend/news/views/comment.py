from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from news.models import Comment, NewsSummary, ArticleStats
from news.serializers.serializers import CommentSerializer
from news.services import comment_service
from django.shortcuts import get_object_or_404
from django.db.models import F
from news.permissions import IsOwnerOrAdminOrReadOnly
import logging

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
        try:
            get_object_or_404(NewsSummary, id=summary_id)
        except NewsSummary.DoesNotExist:
            raise NotFound(
                detail=f"Không tìm thấy tóm tắt với ID: {summary_id}",
                code="summary_not_found")
        return comment_service.get_comments_by_summary_id(summary_id)

    def perform_create(self, serializer):
        summary_id = self.kwargs.get('summary_id')
        try:
            summary = get_object_or_404(NewsSummary, id=summary_id)

            comment_instance = serializer.save(
                user_id=self.request.user.id,
                article_id=summary.article_id)

            if comment_instance and summary.article_id:
                article_stats, created = ArticleStats.objects.get_or_create(
                    article_id=summary.article_id,
                    defaults={'comment_count': 1}
                )

                if not created:
                    ArticleStats.objects.filter(
                        article_id=summary.article_id).update(
                        comment_count=F('comment_count') + 1)
        except Exception as e:
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
            ArticleStats.objects.filter(
                article_id=article_id,
                comment_count__gt=0).update(
                comment_count=F('comment_count') - 1)
