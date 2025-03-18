from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import NewsSource

class Command(BaseCommand):
    help = 'Seed predefined news sources into the database'

    def handle(self, *args, **options):
        sources = [
            {"name": "Báo Mới", "website": "https://baomoi.com"},
            {"name": "VNExpress", "website": "https://vnexpress.net"},
        ]

        try:
            with transaction.atomic():
                self.stdout.write("🗑️  Đang xóa tất cả NewsSource cũ...")
                NewsSource.objects.all().delete()

                self.stdout.write(self.style.NOTICE("⏳ Seeding news sources..."))
                for source in sources:
                    NewsSource.objects.get_or_create(
                        website=source["website"],
                        defaults={"name": source["name"]}
                    )
                    self.stdout.write(self.style.SUCCESS(f"✔ Tạo nguồn tin: {source['name']}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi khi seed news sources: {str(e)}"))
