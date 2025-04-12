import os
from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import User

# Consider loading sensitive data like passwords from environment variables
DEFAULT_PASSWORD = os.environ.get("SEED_USER_DEFAULT_PASSWORD", "password123") # Default if not set

class Command(BaseCommand):
    help = 'Seed predefined users into the database'

    def handle(self, *args, **options):
        USER_DATA = [
            {"username": "admin", "email": "admin@example.com", "password": DEFAULT_PASSWORD, "is_staff": True, "is_superuser": True},
            {"username": "testuser1", "email": "test1@example.com", "password": DEFAULT_PASSWORD},
            {"username": "hunghdg215062", "email": "hdghung2912@gmail.com", "password": DEFAULT_PASSWORD},
        ]

        try:
            with transaction.atomic():
                self.stdout.write("🗑️  Đang xóa tất cả User cũ...")
                # Delete all users before seeding new ones
                User.objects.all().delete()
                self.stdout.write("✔ Đã xóa User cũ.")

                created_count = 0
                for user_data in USER_DATA:
                    username = user_data['username']
                    email = user_data['email']
                    password = user_data['password']
                    is_staff = user_data.get('is_staff', False)
                    is_superuser = user_data.get('is_superuser', False)


                    if not User.objects.filter(username=username).exists() and not User.objects.filter(email=email).exists():
                        if is_superuser:
                             User.objects.create_superuser(
                                username=username,
                                email=email,
                                password=password,
                                # create_superuser sets is_staff and is_superuser to True by default
                            )
                        else:
                            User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                is_staff=is_staff
                            )
                        self.stdout.write(self.style.SUCCESS(f"✔ Đã tạo User: {username}"))
                        created_count += 1
                    else:
                         self.stdout.write(self.style.WARNING(f"ℹ️ User {username} hoặc email {email} đã tồn tại, bỏ qua."))

                if created_count > 0:
                     self.stdout.write(self.style.SUCCESS(f"✅ Đã tạo thành công {created_count} user mới."))
                else:
                     self.stdout.write(self.style.WARNING("Không có user mới nào được tạo."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi khi seed users: {str(e)}")) 