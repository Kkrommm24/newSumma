# backend/news/management/commands/seed_all.py

import logging
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seeds the database with initial data for all relevant models.'

    SEED_COMMANDS = [
        'seed_users',
        'seed_categories',
        'seed_news_sources',
        'seed_vnexpress_tasks',
        'seed_baomoi_tasks',
        'seed_summary_tasks',
        'seed_summary_feedbacks',
        'seed_user_preferences',
        'seed_search_histories',
        # 'seed_comments',
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            'Starting database seeding process...'))

        for command_name in self.SEED_COMMANDS:
            self.stdout.write(
                self.style.HTTP_INFO(f'Running {command_name}...'))
            try:
                call_command(command_name)
                self.stdout.write(self.style.SUCCESS(
                    f'{command_name} completed successfully.'))
            except Exception as e:
                logger.exception(
                    f"An error occurred during command: {command_name}")
                self.stderr.write(
                    self.style.ERROR(f'An error occurred during {command_name}: {e}'))
                self.stdout.write(self.style.WARNING(
                    f'Skipping remaining commands due to error in {command_name}.'))
                break

        self.stdout.write(self.style.SUCCESS(
            'Database seeding process finished.'))
