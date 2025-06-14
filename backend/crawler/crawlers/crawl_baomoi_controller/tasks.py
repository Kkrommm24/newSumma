import logging

from crawler.crawlers.crawl_baomoi_controller.crawler import BaomoiCrawler
from crawler.services.news_service import save_articles_with_categories
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def crawl_baomoi_articles(limit=10):
    logger.info("🔍 Bắt đầu crawl bài viết từ Báo Mới...")
    crawler = BaomoiCrawler()

    articles = crawler.crawl(limit=limit)
    urls_processed = getattr(crawler, 'urls_processed', [])

    if not articles:
        logger.warning("⚠️ Không có bài viết nào được crawl.")
        return 0, urls_processed

    count = save_articles_with_categories(
        "Báo Mới", "https://baomoi.com", articles)
    logger.info("✅ Hoàn tất quá trình crawl và lưu bài viết.")
    return count, urls_processed
