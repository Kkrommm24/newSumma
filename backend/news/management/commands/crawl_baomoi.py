from django.core.management.base import BaseCommand
from news.crawlers.baomoi.tasks import crawl_baomoi_articles
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crawl news articles from BaoMoi and save to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles to crawl (default: 50)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        logger.info(f"🕵️‍♂️ Đang bắt đầu crawl {limit} bài viết từ Báo Mới...")
        try:
            count = crawl_baomoi_articles(limit=limit)
            self.stdout.write(self.style.SUCCESS(f"✅ Đã lưu thêm {count} bài viết từ Báo Mới."))
        except Exception as e:
            logger.error(f"❌ Crawl thất bại: {e}")
            self.stderr.write(self.style.ERROR(f"Lỗi: {e}"))
