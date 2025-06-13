from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Seed periodic task for crawling vnexpress articles'

    def handle(self, *args, **kwargs):
        # Xoá các task cũ có liên quan đến crawl vnexpress
        deleted, _ = PeriodicTask.objects.filter(
            name__icontains='vnexpress').delete()
        self.stdout.write(self.style.WARNING(
            f"🧹 Đã xoá {deleted} task cũ liên quan đến vnexpress."))

        # Tạo schedule mỗi 10 phút
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )

        # Tạo mới task
        PeriodicTask.objects.create(
            name='Crawl vnexpress every 10 minutes',
            interval=schedule,
            task='crawler.crawlers.crawl_vnexpress_controller.tasks.crawl_vnexpress_articles',
            args=json.dumps(
                [10]),
        )

        self.stdout.write(self.style.SUCCESS(
            "✅ Task crawl vnexpress đã được tạo lại thành công!"))
