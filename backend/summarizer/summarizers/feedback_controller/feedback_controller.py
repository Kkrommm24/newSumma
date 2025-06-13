# Giả định import này đúng
from summarizer.services.feedback_service import FeedbackService
import logging

logger = logging.getLogger(__name__)
feedback_service_instance = FeedbackService()


def record_feedback_interface(user, summary_id: str, is_upvote: bool | None):
    try:
        return feedback_service_instance.record_feedback_and_check_threshold(
            user=user,
            summary_id=summary_id,
            is_upvote=is_upvote
        )
    except Exception as e:
        logger.error(
            f"FeedbackController: Error calling record_feedback_and_check_threshold for summary '{summary_id}', user '{user.id if user else None}': {e}",
            exc_info=True)
        raise
