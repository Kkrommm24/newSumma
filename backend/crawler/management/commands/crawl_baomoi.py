from django.core.management.base import BaseCommand
from crawler.crawlers.baomoi.tasks import crawl_baomoi_articles
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
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Hiển thị chi tiết quá trình crawl'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        verbose = options['verbose']
        
        # Thay đổi level logging nếu verbose=True
        if verbose:
            logging.getLogger('news').setLevel(logging.INFO)
            
        logger.info(f"🕵️‍♂️ Đang bắt đầu crawl {limit} bài viết từ Báo Mới...")
        try:
            count, urls_processed = crawl_baomoi_articles(limit=limit)
            logger.info(f"Đã xử lý tổng cộng {len(urls_processed)} URL")
            
            if verbose and urls_processed:
                self.stdout.write("\n--- URLs đã xử lý ---")
                for idx, url_info in enumerate(urls_processed, 1):
                    status = "✅" if url_info.get("success") else "❌"
                    reason = f" - {url_info.get('reason', '')}" if not url_info.get("success") else ""
                    self.stdout.write(f"{idx}. {status} {url_info.get('url')}{reason}")
                self.stdout.write("---------------------\n")
                
            self.stdout.write(self.style.SUCCESS(f"✅ Đã lưu thêm {count} bài viết từ Báo Mới."))
        except Exception as e:
            logger.error(f"❌ Crawl thất bại: {e}")
            self.stderr.write(self.style.ERROR(f"Lỗi: {e}"))
