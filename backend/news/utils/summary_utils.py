import logging
from news.models import NewsSummary, NewsArticle

logger = logging.getLogger(__name__)

def get_latest_summaries(limit=100):
    try:
        summaries = NewsSummary.objects.order_by('-created_at')[:limit]
        return list(summaries)
    except Exception as e:
        logger.error(f"Lỗi khi lấy latest summaries trong utils: {e}")
        return []

def get_articles_for_summaries(summaries):
    if not summaries:
        return {}
    try:
        article_ids = {summary.article_id for summary in summaries}
        articles = NewsArticle.objects.filter(id__in=article_ids)
        return {str(article.id): article for article in articles}
    except Exception as e:
        logger.error(f"Lỗi khi lấy articles cho summaries trong utils: {e}")
        return {} 