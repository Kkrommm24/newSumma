import logging
from uuid import UUID
from news.models import NewsArticle

logger = logging.getLogger(__name__)


class ArticleService:
    def get_article_by_id(self, article_id: str | UUID) -> NewsArticle | None:
        try:
            return NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            logger.warning(
                f"ArticleService: Không tìm thấy bài viết ID {article_id}.")
            return None
        except Exception as e:
            logger.exception(
                f"ArticleService: Lỗi khi lấy bài viết ID {article_id}: {e}")
            return None

    def check_article_exists(self, article_id: str | UUID) -> bool:
        try:
            return NewsArticle.objects.filter(id=article_id).exists()
        except Exception as e:
            # Log lỗi nhưng vẫn trả về False để tránh lỗi không mong muốn ở nơi
            # gọi
            logger.exception(
                f"ArticleService: Lỗi khi kiểm tra bài viết ID {article_id}: {e}")
            return False
