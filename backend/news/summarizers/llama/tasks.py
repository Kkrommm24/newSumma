import django
django.setup()

import logging

from news.summarizers.llama.article_summary import LlamaSummarizer
from news.services.summary_service import SummaryService
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(name='news.summarizers.llama.tasks.generate_article_summaries')
def generate_article_summaries(limit=10):
    """Task tạo summary cho các bài viết chưa có"""
    try:
        logger.info(f"Bắt đầu tạo summary cho tối đa {limit} bài viết...")
        summary_service = SummaryService()
        summarizer = LlamaSummarizer()
        
        articles = summary_service.get_articles_without_summary(limit)
        
        count = 0
        for article in articles:
            try:
                content_to_summarize = f"Tiêu đề: {article.title}\n\n{article.content}"
                
                summary_text = summarizer.summarize(content_to_summarize)
                
                if summary_text:
                    summary = summary_service.create_summary(article.id, summary_text)
                    if summary:
                        count += 1
                    else:
                        logger.warning(f"Không thể tạo summary trong database cho bài viết {article.id}")
                else:
                    logger.warning(f"Không thể tạo tóm tắt cho bài viết {article.id}")              
            except Exception as e:
                logger.exception(f"Lỗi khi xử lý bài viết {article.id}: {str(e)}")
                continue      
        logger.info(f"Đã tạo thành công {count} summaries")
        return count
        
    except Exception as e:
        logger.exception(f"Lỗi trong quá trình tạo summaries: {str(e)}")
        return 0
