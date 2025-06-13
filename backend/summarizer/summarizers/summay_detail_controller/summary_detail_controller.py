from summarizer.services import summary_detail_service
import logging

logger = logging.getLogger(__name__)


def get_summary_detail_interface(summary_id: str):
    try:
        return summary_detail_service.get_summary_by_id(summary_id)
    except Exception as e:
        logger.error(
            f"SummaryDetailController: Error calling get_summary_by_id for summary_id '{summary_id}': {e}",
            exc_info=True)
        raise


def get_article_summary_interface(article_id: str):
    try:
        return summary_detail_service.get_latest_summary_by_article_id(
            article_id)
    except Exception as e:
        logger.error(
            f"SummaryDetailController: Error calling get_latest_summary_by_article_id for article_id '{article_id}': {e}",
            exc_info=True)
        raise
