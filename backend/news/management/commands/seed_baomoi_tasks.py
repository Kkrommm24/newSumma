from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Seed periodic task for crawling baomoi articles'

    def handle(self, *args, **kwargs):
        # Xoá các task cũ có liên quan đến crawl baomoi
        deleted, _ = PeriodicTask.objects.filter(name__icontains='baomoi').delete()
        self.stdout.write(self.style.WARNING(f"🧹 Đã xoá {deleted} task cũ liên quan đến baomoi."))

        # Tạo schedule mỗi 10 phút
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )

        # Tạo mới task
        PeriodicTask.objects.create(
            name='Crawl baomoi every 10 minutes',
            interval=schedule,
            task='news.crawlers.baomoi.tasks.crawl_baomoi_articles',
            args=json.dumps([10]),
        )

        self.stdout.write(self.style.SUCCESS("✅ Task crawl baomoi đã được tạo lại thành công!"))
