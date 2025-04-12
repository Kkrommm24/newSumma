# backend/news/management/commands/seed_all.py

from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Seed all initial data by calling other seed commands'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Bắt đầu seed toàn bộ dữ liệu...\n"))

        self.stdout.write(self.style.NOTICE("👉 Seed categories..."))
        call_command('seed_categories')

        self.stdout.write(self.style.NOTICE("\n👉 Seed users..."))
        call_command('seed_users')

        self.stdout.write(self.style.NOTICE("\n👉 Seed user preferences..."))
        call_command('seed_user_preferences')

        self.stdout.write(self.style.NOTICE("\n👉 Seed search history..."))
        call_command('seed_search_histories')

        self.stdout.write(self.style.NOTICE("\n👉 Seed news sources..."))
        call_command('seed_news_sources')

        self.stdout.write(self.style.NOTICE("\n👉 Seed baomoi tasks..."))
        call_command('seed_baomoi_tasks')

        self.stdout.write(self.style.NOTICE("\n👉 Seed vnexpress tasks..."))
        call_command('seed_vnexpress_tasks')
        
        self.stdout.write(self.style.NOTICE("\n👉 Seed summary tasks..."))
        call_command('seed_summary_tasks')

        self.stdout.write(self.style.SUCCESS("\n✅ Đã seed xong tất cả dữ liệu!"))
