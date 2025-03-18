import logging

from news.crawlers.baomoi.crawler import BaomoiCrawler
from news.services.news_service import save_articles_with_categories
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def crawl_baomoi_articles(limit=10) -> int:
    logger.info("🔍 Bắt đầu crawl bài viết từ Báo Mới...")
    crawler = BaomoiCrawler()

    articles = crawler.crawl(limit=limit)

    if not articles:
        logger.warning("⚠️ Không có bài viết nào được crawl.")
        return 0

    count = save_articles_with_categories("Báo Mới", "https://baomoi.com", articles)
    logger.info("✅ Hoàn tất quá trình crawl và lưu bài viết.")
    return count
    
