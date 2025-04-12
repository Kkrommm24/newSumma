import logging
from news.models import NewsSummary, NewsArticle
from django.db.models import Exists, OuterRef
from django.contrib.postgres.search import SearchVector
from summarizer.summarizers.llama.article_summary import LlamaSummarizer
import gc
import torch
from ..utils.validators import is_mostly_uppercase, contains_numbered_list

logger = logging.getLogger(__name__)

class SummaryService:
    fts_search_config = 'vietnamese'
    _summarizer_instance = None

    def __init__(self):
        pass

    def _get_summarizer(self):
        if self._summarizer_instance is None:
            try:
                self._summarizer_instance = LlamaSummarizer()
                logger.info(f"Service: LlamaSummarizer initialized on device: {self._summarizer_instance.device}")
            except Exception as e:
                 logger.exception("Service: Failed to initialize LlamaSummarizer.")
                 raise e
        return self._summarizer_instance

    def _cleanup_memory(self):
        """Dọn dẹp bộ nhớ GPU nếu có."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def process_and_save_summary(self, article: NewsArticle) -> NewsSummary | None:
        if not article:
            return None
        try:
            logger.info(f"Service: Processing article ID {article.id} for summary.")
            summarizer = self._get_summarizer()

            self._cleanup_memory()
            summary_text = summarizer.summarize(article.content)
            self._cleanup_memory()
            
            if not summary_text:
                logger.warning(f"Service: Summarizer returned empty for article ID {article.id}.")
                return None

            if is_mostly_uppercase(summary_text):
                logger.warning(f"Service: Summary for article ID {article.id} discarded (mostly uppercase).")
                return None
            if contains_numbered_list(summary_text):
                logger.warning(f"Service: Summary for article ID {article.id} discarded (contains numbered list).")
                return None

            search_vector = SearchVector(summary_text, config=self.fts_search_config)
            summary, created = NewsSummary.objects.update_or_create(
                article_id=article.id,
                defaults={
                    'summary_text': summary_text,
                }
            )
            
            log_action = "CREATED" if created else "UPDATED"
            logger.info(f"Service: Successfully {log_action} summary and vector for article ID {article.id}")
            return summary

        except Exception as e:
            logger.exception(f"Service: Error processing article ID {article.id}: {e}")
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
            
            logger.info(f"Service: Tìm thấy {articles.count()} bài viết cần tóm tắt (limit {limit})")
            return articles
            
        except Exception as e:
            logger.exception(f"Lỗi khi lấy danh sách bài viết: {str(e)}")
            return [] 