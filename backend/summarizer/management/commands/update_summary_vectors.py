import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Value
from django.contrib.postgres.search import SearchVector
from news.models import NewsSummary, NewsArticle
from tqdm import tqdm

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Updates the search_vector for all existing NewsSummary entries.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting update of search vectors for NewsSummary...'))

        summaries_to_update = NewsSummary.objects.all()
        articles = NewsArticle.objects.in_bulk(summaries_to_update.values_list('article_id', flat=True))
        
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for summary in tqdm(summaries_to_update, desc="Updating vectors"):
                article = articles.get(summary.article_id)
                
                if not article:
                    self.stdout.write(self.style.WARNING(f'Skipping summary {summary.id}: Corresponding NewsArticle {summary.article_id} not found.'))
                    skipped_count += 1
                    continue
                
                try:
                    new_vector = (
                        SearchVector('summary_text', weight='A', config='vietnamese') + 
                        SearchVector(Value(article.title), weight='B', config='vietnamese')
                    )
                    
                    summary.search_vector = new_vector
                    summary.save(update_fields=['search_vector'])
                    updated_count += 1
                    
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error updating vector for summary {summary.id}: {e}'))
                    raise e

        self.stdout.write(self.style.SUCCESS(f'Successfully updated search vectors for {updated_count} summaries.'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped {skipped_count} summaries due to missing articles.')) 