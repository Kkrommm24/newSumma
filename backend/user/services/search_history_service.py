import logging
from news.models import SearchHistory
from django.db import transaction
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def get_user_search_history(user_id):
    if not user_id:
        logger.warning("Attempted to get search history with no user ID.")
        return SearchHistory.objects.none()

    try:
        return SearchHistory.objects.filter(user_id=user_id).order_by('-searched_at')
    except Exception as e:
        logger.error(f"Database error fetching search history for user {user_id}: {e}", exc_info=True)
        raise


def add_user_search_history(user_id, query: str) -> SearchHistory:
    if not user_id or not query or not query.strip():
        raise ValueError("User ID and a non-empty query are required to add search history.")

    try:
        new_history = SearchHistory.objects.create(
            user_id=user_id,
            query=query.strip()
        )
        logger.info(f"Added search history for user {user_id}: '{query}'")
        return new_history
    except Exception as e:
        logger.error(f"Database error adding search history for user {user_id}: {e}", exc_info=True)
        raise


def delete_search_histories(user_id, queries_to_delete: list[str]) -> int:
    if not user_id or not queries_to_delete:
        logger.warning("User ID or queries list to delete is empty.")
        return 0

    try:
        with transaction.atomic():
            deleted_count, _ = SearchHistory.objects.filter(
                user_id=user_id,
                query__in=queries_to_delete
            ).delete()
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} search history entries for user {user_id}.")
            else:
                logger.info(f"No matching search history entries found to delete for user {user_id} with queries: {queries_to_delete}")
            
            return deleted_count

    except Exception as e:
        logger.error(f"Database error deleting search history for user {user_id}: {e}", exc_info=True)
        raise 
