from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from news.models import User, SearchHistory
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed SearchHistory records for existing users'

    def handle(self, *args, **options):
        SEARCH_HISTORY_DATA = {
            "testuser1": [
                "Django Rest Framework",
                "React Native",
                "AI news"],
            "hunghdg215062": [
                "Premier League",
                "Lãi suất ngân hàng",
                "Giá vàng",
                "World Cup 2026"],
            "admin": [
                "Celery Beat schedule",
                "PostgreSQL performance"],
        }

        created_count = 0
        history_to_create = []
        now = timezone.now()

        self.stdout.write("🌱 Bắt đầu seed SearchHistory...")

        # Clear existing history for simplicity in testing, optional
        self.stdout.write("🗑️  Đang xóa SearchHistory cũ...")
        SearchHistory.objects.all().delete()
        self.stdout.write("✔ Đã xóa SearchHistory cũ.")

        for username, queries in SEARCH_HISTORY_DATA.items():
            try:
                user = User.objects.get(username=username)
                for i, query in enumerate(queries):
                    # Create history entries with slightly different timestamps
                    # Make timestamps distinct
                    search_time = now - timedelta(minutes=i * 5 + len(queries))
                    history_to_create.append(
                        SearchHistory(
                            user_id=user.id,
                            query=query,
                            searched_at=search_time))
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f"❌ User '{username}' không tồn tại. Bỏ qua seeding search history."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"❌ Lỗi khi chuẩn bị search history cho user '{username}': {str(e)}"))

        if history_to_create:
            try:
                with transaction.atomic():
                    SearchHistory.objects.bulk_create(history_to_create)
                    created_count = len(history_to_create)
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Đã tạo thành công {created_count} bản ghi SearchHistory."))
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"❌ Lỗi khi bulk create SearchHistory: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING(
                "Không có bản ghi SearchHistory nào được tạo."))
