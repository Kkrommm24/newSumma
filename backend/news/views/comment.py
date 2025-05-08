from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from news.models import Comment, NewsSummary
from news.serializers.serializers import CommentSerializer
from news.services import comment_service
from django.shortcuts import get_object_or_404
from news.permissions import IsOwnerOrAdminOrReadOnly

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        summary_id = self.kwargs.get('summary_id')
        try:
            get_object_or_404(NewsSummary, id=summary_id)
        except NewsSummary.DoesNotExist:
            raise NotFound(detail=f"Không tìm thấy tóm tắt với ID: {summary_id}", code="summary_not_found")
        return comment_service.get_comments_by_summary_id(summary_id)

    def perform_create(self, serializer):
        summary_id = self.kwargs.get('summary_id')
        summary = get_object_or_404(NewsSummary, id=summary_id)
        serializer.save(user_id=self.request.user.id, article_id=summary.article_id)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    lookup_field = 'id'
