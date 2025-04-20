import logging
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from uuid import UUID

from news.models import NewsSummary, SummaryFeedback, User

logger = logging.getLogger(__name__)

MIN_TOTAL_VOTES_FOR_RATIO_CHECK = 10
DOWNVOTE_RATIO_THRESHOLD = 0.7

class FeedbackService:
    def record_feedback_and_check_threshold(self, user: User, summary_id: UUID | str, is_upvote: bool) -> tuple[NewsSummary | None, bool, int | None, int | None]:
        trigger_resummarize = False
        summary_object = None
        final_upvotes = None
        final_downvotes = None

        try:
            with transaction.atomic():
                summary = NewsSummary.objects.select_for_update().get(id=summary_id)
                summary_object = summary
                initial_upvotes = summary.upvotes
                initial_downvotes = summary.downvotes

                feedback, created = SummaryFeedback.objects.update_or_create(
                    user_id=user.id,
                    summary_id=summary.id,
                    defaults={'is_upvote': is_upvote}
                )

                needs_update = False
                upvote_change = 0
                downvote_change = 0

                if created:
                    needs_update = True
                    if is_upvote:
                        upvote_change = 1
                    else:
                        downvote_change = 1
                elif feedback.is_upvote != is_upvote:
                    needs_update = True
                    if is_upvote:
                        upvote_change = 1
                        downvote_change = -1
                    else:
                        upvote_change = -1
                        downvote_change = 1

                final_upvotes = initial_upvotes + upvote_change
                final_downvotes = initial_downvotes + downvote_change

                if needs_update:
                    NewsSummary.objects.filter(id=summary.id).update(
                        upvotes=F('upvotes') + upvote_change,
                        downvotes=F('downvotes') + downvote_change,
                        updated_at=timezone.now()
                    )

            if summary_object:
                total_votes = final_upvotes + final_downvotes
                if total_votes >= MIN_TOTAL_VOTES_FOR_RATIO_CHECK:
                    if final_downvotes > 0: 
                        downvote_ratio = final_downvotes / total_votes
                        if downvote_ratio >= DOWNVOTE_RATIO_THRESHOLD: 
                            trigger_resummarize = True
                return summary_object, trigger_resummarize, final_upvotes, final_downvotes
            else:
                 return None, False, None, None 

        except NewsSummary.DoesNotExist:
            logger.warning(f"FeedbackService: Không tìm thấy Summary ID {summary_id}.")
            return None, False, None, None
        except ZeroDivisionError:
             logger.error(f"FeedbackService: Unexpected ZeroDivisionError for summary {summary_id}", exc_info=True)
             return summary_object, False, final_upvotes, final_downvotes
        except Exception as e:
            logger.exception(f"FeedbackService: Lỗi khi xử lý feedback cho summary {summary_id}: {e}")
            return None, False, None, None 