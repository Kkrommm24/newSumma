from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Seed periodic task for sumarizing articles'

    def handle(self, *args, **kwargs):
        deleted, _ = PeriodicTask.objects.filter(name__icontains='Summarizing').delete()
        self.stdout.write(self.style.WARNING(f"🧹 Đã xoá {deleted} task cũ liên quan đến summary."))

        # Tạo schedule mỗi 10 phút
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )

        # Tạo mới task
        PeriodicTask.objects.create(
            name='Summarizing every 10 minutes',
            interval=schedule,
            task='summarizer.summarizers.llama.tasks.generate_article_summaries',
            args=json.dumps([10]),
        )

        self.stdout.write(self.style.SUCCESS("✅ Task summary đã được tạo lại thành công!"))
