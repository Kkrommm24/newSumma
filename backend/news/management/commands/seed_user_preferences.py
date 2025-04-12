from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import User, UserPreference
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seed UserPreferences with favorite keywords for existing users'

    def handle(self, *args, **options):
        USER_PREFERENCES_DATA = {
            "testuser1": ["công nghệ", "AI", "startup"],
            "hunghdg215062": ["bóng đá", "chuyển nhượng", "thể thao", "kinh tế vĩ mô", "U17"],
            # "admin": [], # Example: Admin has no specific keywords initially
        }

        created_count = 0
        updated_count = 0

        self.stdout.write("🌱 Bắt đầu seed UserPreferences...")

        try:
            with transaction.atomic():
                for username, keywords in USER_PREFERENCES_DATA.items():
                    try:
                        user = User.objects.get(username=username)

                        preference, created = UserPreference.objects.update_or_create(
                            user_id=user.id,
                            defaults={'favorite_keywords': keywords}
                        )

                        if created:
                            self.stdout.write(self.style.SUCCESS(f"✔ Đã tạo Preference cho user: {username} với keywords: {keywords}"))
                            created_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"ℹ️ Đã cập nhật Preference cho user: {username} với keywords: {keywords}"))
                            updated_count += 1

                    except User.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f"❌ User '{username}' không tồn tại. Bỏ qua seeding preference."))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"❌ Lỗi khi seeding preference cho user '{username}': {str(e)}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi transaction khi seeding preferences: {str(e)}"))

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Đã tạo thành công {created_count} UserPreference mới."))
        if updated_count > 0:
             self.stdout.write(self.style.SUCCESS(f"✅ Đã cập nhật thành công {updated_count} UserPreference."))
        if created_count == 0 and updated_count == 0:
             self.stdout.write(self.style.WARNING("Không có UserPreference nào được tạo hoặc cập nhật."))
