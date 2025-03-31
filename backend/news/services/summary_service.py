import logging
from news.models import NewsSummary, NewsArticle
from django.db.models import Exists, OuterRef

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self):
        pass
    
    def create_summary(self, article_id: str, summary_text: str) -> NewsSummary:
        try:
            summary = NewsSummary.objects.create(
                article_id=article_id,
                summary_text=summary_text,
                upvotes=0,
                downvotes=0
            )
            return summary
        except Exception as e:
            logger.exception(f"Lỗi khi tạo summary cho bài viết ID {article_id}: {str(e)}")
            return None
    
    def get_articles_without_summary(self, limit: int = 10):
        try:
            articles = NewsArticle.objects.filter(
                ~Exists(
                    NewsSummary.objects.filter(
                        article_id=OuterRef('id')
                    )
                )
            ).order_by('-published_at')[:limit]
            
            logger.info(f"Tìm thấy {articles.count()} bài viết cần tóm tắt")
            return articles
            
        except Exception as e:
            logger.exception(f"Lỗi khi lấy danh sách bài viết: {str(e)}")
            return [] 