import logging
from user.models import SearchHistory
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.exceptions import APIException
from recommender.services.recommend_service import update_user_search_history_rankings
from typing import List

logger = logging.getLogger(__name__)


class SearchHistoryException(APIException):
    status_code = 500
    default_detail = 'Đã xảy ra lỗi khi xử lý lịch sử tìm kiếm.'
    default_code = 'search_history_error'


class SearchHistoryService:
    @staticmethod
    def get_user_search_history(user_id: str) -> List[SearchHistory]:
        if not user_id:
            return SearchHistory.objects.none()

        try:
            return SearchHistory.objects.filter(
                user_id=user_id).order_by('-searched_at')
        except Exception as e:
            raise SearchHistoryException(
                f"Lỗi khi lấy lịch sử tìm kiếm: {str(e)}")

    @staticmethod
    def add_user_search_history(user_id: str, query: str) -> SearchHistory:
        stripped_query = query.strip()
        if not user_id or not stripped_query:
            raise ValueError("User ID and a non-empty query are required.")

        try:
            history_entry, created = SearchHistory.objects.update_or_create(
                user_id=user_id,
                query=stripped_query,
                defaults={'searched_at': timezone.now()}
            )

            if user_id:
                try:
                    update_user_search_history_rankings(user_id=user_id)
                except Exception as e_rank:
                    logger.error(
                        f"Error triggering summary search history ranking update for user {user_id}: {e_rank}",
                        exc_info=True)

            return history_entry
        except Exception as e:
            raise SearchHistoryException(
                f"Lỗi khi lưu lịch sử tìm kiếm: {str(e)}")

    @staticmethod
    def delete_search_histories(
            user_id: str,
            queries_to_delete: List[str]) -> int:
        if not user_id or not queries_to_delete:
            return 0

        try:
            with transaction.atomic():
                deleted_count, _ = SearchHistory.objects.filter(
                    user_id=user_id,
                    query__in=queries_to_delete
                ).delete()

                return deleted_count

        except Exception as e:
            raise SearchHistoryException(
                f"Lỗi khi xóa lịch sử tìm kiếm: {str(e)}")
