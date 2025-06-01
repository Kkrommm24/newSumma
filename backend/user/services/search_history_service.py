import logging
from user.models import SearchHistory
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class SearchHistoryException(APIException):
    status_code = 500
    default_detail = 'Đã xảy ra lỗi khi xử lý lịch sử tìm kiếm.'
    default_code = 'search_history_error'


def get_user_search_history(user_id):
    if not user_id:
        return SearchHistory.objects.none()

    try:
        return SearchHistory.objects.filter(
            user_id=user_id).order_by('-searched_at')
    except Exception as e:
        raise SearchHistoryException(f"Lỗi khi lấy lịch sử tìm kiếm: {str(e)}")


def add_user_search_history(user_id, query: str) -> SearchHistory:
    stripped_query = query.strip()
    if not user_id or not stripped_query:
        raise ValueError("User ID and a non-empty query are required.")

    try:
        history_entry, created = SearchHistory.objects.update_or_create(
            user_id=user_id,
            query=stripped_query,
            defaults={'searched_at': timezone.now()}
        )

        return history_entry
    except Exception as e:
        raise SearchHistoryException(f"Lỗi khi lưu lịch sử tìm kiếm: {str(e)}")


def delete_search_histories(user_id, queries_to_delete: list[str]) -> int:
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
        raise SearchHistoryException(f"Lỗi khi xóa lịch sử tìm kiếm: {str(e)}")
