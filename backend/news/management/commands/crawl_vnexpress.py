from django.core.management.base import BaseCommand
from news.crawlers.vnexpress.tasks import crawl_vnexpress_articles
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crawl news articles from VNExpress and save to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles to crawl (default: 50)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        logger.info(f"🕵️‍♂️ Đang bắt đầu crawl {limit} bài viết từ VNExpress...")
        try:
            count = crawl_vnexpress_articles(limit=limit)
            self.stdout.write(self.style.SUCCESS(f"✅ Đã lưu thêm {count} bài viết từ VNExpress."))
        except Exception as e:
            logger.error(f"❌ Crawl thất bại: {e}")
            self.stderr.write(self.style.ERROR(f"Lỗi: {e}"))
