import random
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Q, OuterRef, Subquery

from news.models import NewsSummary, User, SummaryFeedback, NewsArticle

logger = logging.getLogger(__name__) 

# Số lượng vote cố định cho summary đầu tiên
FIXED_UPVOTES = 3
FIXED_DOWNVOTES = 6
FIXED_TOTAL_USERS_NEEDED = FIXED_UPVOTES + FIXED_DOWNVOTES

class Command(BaseCommand):
    help = 'Seeds the database with summary feedback, ensuring one summary has a specific vote count (3 up, 6 down).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed summary feedback...'))

        try:
            # Subquery to get the published_at of the related NewsArticle
            article_published_at_subquery = NewsArticle.objects.filter(
                id=OuterRef('article_id')
            ).values('published_at')[:1]

            summaries_to_process = list(
                NewsSummary.objects.annotate(
                    article_published_at_val=Subquery(article_published_at_subquery)
                ).order_by('-article_published_at_val')[:10]
            )
            # Loại bỏ user 'hunghdg215062' trước khi lấy danh sách ngẫu nhiên
            users = list(User.objects.exclude(username='hunghdg215062').order_by('?')[:20])

            if not summaries_to_process:
                self.stdout.write(self.style.WARNING('No NewsSummary found. Please seed summaries first.'))
                return
            if len(users) < FIXED_TOTAL_USERS_NEEDED:
                self.stdout.write(self.style.WARNING(f'Need at least {FIXED_TOTAL_USERS_NEEDED} users for fixed vote seeding, found {len(users)}. Please seed more users.'))
                return

            feedback_created_count = 0
            summaries_updated_count = 0

            with transaction.atomic():
                SummaryFeedback.objects.all().delete()
                self.stdout.write(self.style.WARNING('Deleted existing summary feedback.'))
                
                summary_ids_to_reset = [s.id for s in summaries_to_process]
                reset_count = NewsSummary.objects.filter(id__in=summary_ids_to_reset).update(upvotes=0, downvotes=0)
                self.stdout.write(self.style.WARNING(f'Reset vote counts for {reset_count} summaries.'))

                fixed_vote_users = random.sample(users, FIXED_TOTAL_USERS_NEEDED)
                remaining_users = [user for user in users if user not in fixed_vote_users]

                target_summary = summaries_to_process[0]
                self.stdout.write(self.style.HTTP_INFO(f'Assigning fixed votes (Up:{FIXED_UPVOTES}/Down:{FIXED_DOWNVOTES}) to summary {target_summary.id}'))
                users_for_upvote = fixed_vote_users[:FIXED_UPVOTES]
                users_for_downvote = fixed_vote_users[FIXED_UPVOTES:]

                for user in users_for_upvote:
                    SummaryFeedback.objects.update_or_create(
                        user_id=user.id, summary_id=target_summary.id, defaults={'is_upvote': True}
                    )
                    feedback_created_count += 1
                for user in users_for_downvote:
                     SummaryFeedback.objects.update_or_create(
                        user_id=user.id, summary_id=target_summary.id, defaults={'is_upvote': False}
                    )
                     feedback_created_count += 1

                if len(summaries_to_process) > 1:
                    available_random_users = remaining_users if remaining_users else users
                    for i, summary in enumerate(summaries_to_process[1:], start=1):
                        if not available_random_users:
                            self.stdout.write(self.style.WARNING(f'No more users available for random voting on summary {i+1}.'))
                            continue 
                            
                        max_random_votes = min(len(available_random_users), 15)
                        if max_random_votes <= 0 : continue
                        actual_min_votes = min(5, max_random_votes)
                        num_feedback = random.randint(actual_min_votes, max_random_votes)
                        
                        selected_users = random.sample(available_random_users, num_feedback)
                        
                        self.stdout.write(self.style.HTTP_INFO(f'Assigning {num_feedback} random votes to summary {summary.id}'))
                        for user in selected_users:
                            is_upvote = random.choice([True, True, False])
                            SummaryFeedback.objects.update_or_create(
                                user_id=user.id,
                                summary_id=summary.id,
                                defaults={'is_upvote': is_upvote}
                            )
                            feedback_created_count += 1
                
                for summary in summaries_to_process:
                    feedback_counts = SummaryFeedback.objects.filter(summary_id=summary.id).aggregate(
                        upvotes=Count('id', filter=Q(is_upvote=True)),
                        downvotes=Count('id', filter=Q(is_upvote=False))
                    )
                    
                    updated_rows = NewsSummary.objects.filter(id=summary.id).update(
                        upvotes = feedback_counts.get('upvotes', 0),
                        downvotes = feedback_counts.get('downvotes', 0)
                    )
                    if updated_rows > 0:
                        summaries_updated_count += 1

            self.stdout.write(self.style.SUCCESS(f'Successfully created {feedback_created_count} feedback entries.'))
            self.stdout.write(self.style.SUCCESS(f'Successfully updated vote counts for {summaries_updated_count} summaries.'))

        except ImportError:
            self.stderr.write(self.style.ERROR("Error importing models. Make sure your Django environment is set up correctly."))
        except Exception as e:
            logger.exception("An error occurred during feedback seeding.") 
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}')) 