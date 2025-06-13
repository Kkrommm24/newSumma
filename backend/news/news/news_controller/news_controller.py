from news.services import comment_service
from summarizer.models import NewsSummary # Cần cho get_comments_interface để check summary tồn tại
from django.shortcuts import get_object_or_404 # Cần cho get_comments_interface
from rest_framework.exceptions import NotFound # Cần cho get_comments_interface


def get_comments_interface(summary_id: str):
    try:
        get_object_or_404(NewsSummary, id=summary_id)
    except NewsSummary.DoesNotExist:
        raise NotFound(
            detail=f"Không tìm thấy tóm tắt với ID: {summary_id}",
            code="summary_not_found")
    return comment_service.get_comments_by_summary_id(summary_id)


def handle_new_comment_stats_interface(article_id: str):
    if not article_id:
        return 
    comment_service.update_stats_for_new_comment(article_id)


def handle_deleted_comment_stats_interface(article_id: str):
    if not article_id:
        return
    comment_service.update_stats_for_deleted_comment(article_id)
