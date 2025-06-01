import logging
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from uuid import UUID
from typing import Optional

from summarizer.models import NewsSummary, SummaryFeedback
from user.models import User

logger = logging.getLogger(__name__)

MIN_TOTAL_VOTES_FOR_RATIO_CHECK = 10
DOWNVOTE_RATIO_THRESHOLD = 0.7


class FeedbackService:
    def record_feedback_and_check_threshold(self,
                                            user: User,
                                            summary_id: UUID | str,
                                            is_upvote: Optional[bool]) -> tuple[NewsSummary | None,
                                                                                bool,
                                                                                int | None,
                                                                                int | None]:
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

                upvote_change = 0
                downvote_change = 0
                needs_update = False

                existing_feedback = SummaryFeedback.objects.filter(
                    user_id=user.id, summary_id=summary.id).first()

                if is_upvote is None:
                    if existing_feedback:
                        needs_update = True
                        if existing_feedback.is_upvote:
                            upvote_change = -1
                        else:
                            downvote_change = -1
                        existing_feedback.delete()
                        logger.info(
                            f"Service: User {user.id} removed vote for summary {summary.id}.")

                else:
                    if existing_feedback:
                        if existing_feedback.is_upvote != is_upvote:
                            needs_update = True
                            if is_upvote:
                                upvote_change = 1
                                downvote_change = -1
                            else:
                                upvote_change = -1
                                downvote_change = 1
                            existing_feedback.is_upvote = is_upvote
                            existing_feedback.save(
                                update_fields=['is_upvote', 'updated_at'])
                            logger.info(
                                f"Service: User {user.id} changed vote to {is_upvote} for summary {summary.id}.")

                    else:
                        needs_update = True
                        if is_upvote:
                            upvote_change = 1
                        else:
                            downvote_change = 1
                        SummaryFeedback.objects.create(
                            user_id=user.id,
                            summary_id=summary.id,
                            is_upvote=is_upvote
                        )
                        logger.info(
                            f"Service: User {user.id} added vote {is_upvote} for summary {summary.id}.")

                final_upvotes = initial_upvotes + upvote_change
                final_downvotes = initial_downvotes + downvote_change

                if needs_update:
                    NewsSummary.objects.filter(id=summary.id).update(
                        upvotes=F('upvotes') + upvote_change,
                        downvotes=F('downvotes') + downvote_change,
                        updated_at=timezone.now()
                    )
                    logger.info(
                        f"Service: Updated counts for summary {summary.id}: Up {final_upvotes}, Down {final_downvotes}.")

            if summary_object:
                total_votes = final_upvotes + final_downvotes
                if total_votes >= MIN_TOTAL_VOTES_FOR_RATIO_CHECK:
                    if final_downvotes > 0:
                        downvote_ratio = final_downvotes / total_votes
                        if downvote_ratio >= DOWNVOTE_RATIO_THRESHOLD:
                            trigger_resummarize = True
                            logger.info(
                                f"Service: Downvote threshold reached for summary {summary_id}. Triggering re-summarization.")
                return summary_object, trigger_resummarize, final_upvotes, final_downvotes
            else:
                logger.error(
                    f"Service: summary_object became None unexpectedly for {summary_id}")
                return None, False, None, None

        except NewsSummary.DoesNotExist:
            logger.warning(
                f"FeedbackService: Không tìm thấy Summary ID {summary_id}.")
            return None, False, None, None
        except ZeroDivisionError:
            logger.error(
                f"FeedbackService: Unexpected ZeroDivisionError for summary {summary_id}",
                exc_info=True)
            return summary_object, False, final_upvotes, final_downvotes
        except Exception as e:
            logger.exception(
                f"FeedbackService: Lỗi khi xử lý feedback cho summary {summary_id}: {e}")
            return None, False, None, None
