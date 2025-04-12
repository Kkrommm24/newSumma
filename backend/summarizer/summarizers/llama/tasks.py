import django
django.setup()

import logging
import torch
import gc

from celery import shared_task
from summarizer.services.summary_service import SummaryService
from summarizer.services.article_service import ArticleService

logger = logging.getLogger(__name__)

summary_service = SummaryService()
article_service = ArticleService()

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_article_summaries(self, limit=10):
    logger.info(f"Task started: Tạo tóm tắt cho tối đa {limit} bài viết.")
    processed_count = 0
    success_count = 0
    
    try:
        articles_to_process = summary_service.get_articles_without_summary(limit=limit)

        if not articles_to_process:
            return {'processed': 0, 'success': 0}

        total_articles = len(articles_to_process)

        for i, article in enumerate(articles_to_process):
            logger.info(f"Task: Đang yêu cầu xử lý bài viết {i+1}/{total_articles} (ID: {article.id})")
            try:
                result_summary = summary_service.process_and_save_summary(article)
                processed_count += 1
                if result_summary:
                    success_count += 1
                    logger.info(f"Task: Đã xử lý thành công bài viết ID: {article.id}")
                else:
                    logger.warning(f"Task: Service không thể xử lý/lưu summary cho bài viết ID: {article.id}")

            except Exception as exc_inner:
                logger.error(f"Task: Lỗi nghiêm trọng khi xử lý bài viết ID {article.id}: {exc_inner}", exc_info=True)
                processed_count += 1
        
        logger.info(f"Task finished: Đã xử lý {processed_count}/{total_articles} yêu cầu, thành công {success_count}.")
        return {'processed': processed_count, 'success': success_count}

    except Exception as exc_outer:
        logger.error(f"Task failed (outer scope): {exc_outer}", exc_info=True)
        try:
            self.retry(exc=exc_outer)
        except Exception as retry_exc:
             logger.error(f"Task retry failed: {retry_exc}")
        return {'processed': processed_count, 'success': success_count, 'error': str(exc_outer)} # Trả về lỗi

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def summarize_single_article_task(self, article_id_str: str):
    """Celery task để tóm tắt một bài viết cụ thể."""
    logger.info(f"Single Task started: Tóm tắt bài viết ID {article_id_str}")
    
    try:
        article = article_service.get_article_by_id(article_id_str)
        
        if not article:
            logger.error(f"Single Task: Service không tìm thấy bài viết ID {article_id_str}. Task kết thúc.")
            return {'status': 'error', 'message': 'Article not found by service'}

        result_summary = summary_service.process_and_save_summary(article)
        
        if result_summary:
            logger.info(f"Single Task: Đã xử lý thành công bài viết ID: {article_id_str}")
            return {'status': 'success', 'summary_id': str(result_summary.id)}
        else:
            logger.error(f"Single Task: SummaryService không thể xử lý/lưu summary cho bài viết ID: {article_id_str}.")
            try:
                self.retry(countdown=15)
            except Exception as retry_exc:
                logger.error(f"Single Task retry failed: {retry_exc}")
            return {'status': 'error', 'message': 'Failed to process or save summary via service'}

    except Exception as exc:
        logger.error(f"Single Task failed unexpectedly for article {article_id_str}: {exc}", exc_info=True)
        try:
            self.retry(exc=exc)
        except Exception as retry_exc:
             logger.error(f"Single Task retry failed: {retry_exc}")
        return {'status': 'error', 'message': f'Unexpected error: {exc}'}
