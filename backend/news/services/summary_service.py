from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from news.models import NewsArticle
from summarizer.models import NewsSummary


def get_summary_by_id(summary_id: str):
    try:
        summary = get_object_or_404(NewsSummary, id=summary_id)
        return summary
    except NewsSummary.DoesNotExist:
        raise NotFound(
            detail=f"Không tìm thấy tóm tắt với ID: {summary_id}",
            code="summary_not_found")


def get_latest_summary_by_article_id(article_id: str):
    try:
        article = get_object_or_404(NewsArticle, id=article_id)
    except NewsArticle.DoesNotExist:
        raise NotFound(
            detail=f"Không tìm thấy bài viết với ID: {article_id}",
            code="article_not_found")

    summary = NewsSummary.objects.filter(
        article_id=article_id).order_by('-created_at').first()

    if not summary:
        raise NotFound(
            detail=f"Không tìm thấy tóm tắt cho bài viết ID: {article_id}",
            code="summary_not_found")

    return summary, article
