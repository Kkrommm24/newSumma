from summarizer.services import search_service
import logging

logger = logging.getLogger(__name__)


def search_summaries_interface(query_string: str):
    try:
        return search_service.search_summaries_with_articles(query_string)
    except Exception as e:
        logger.error(
            f"SearchController: Error calling search_summaries_with_articles for query '{query_string}': {e}",
            exc_info=True)
        raise
