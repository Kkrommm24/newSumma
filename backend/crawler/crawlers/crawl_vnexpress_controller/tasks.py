import logging

from crawler.crawlers.crawl_vnexpress_controller.crawler import VNExpressCrawler
from crawler.services.news_service import save_articles_with_categories
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def crawl_vnexpress_articles(limit=10):
    logger.info("🔍 Bắt đầu crawl bài viết từ VNExpress...")
    crawler = VNExpressCrawler()

    articles = crawler.crawl(limit=limit)
    urls_processed = getattr(crawler, 'urls_processed', [])

    if not articles:
        logger.warning("⚠️ Không có bài viết nào được crawl.")
        return 0, urls_processed

    count = save_articles_with_categories(
        "VNExpress", "https://vnexpress.net", articles)
    logger.info("✅ Hoàn tất quá trình crawl và lưu bài viết.")
    return count, urls_processed
