import logging
from rest_framework.exceptions import APIException
from user.services.search_history_service import SearchHistoryService
from recommender.services.recommend_service import update_user_search_history_rankings
from typing import List
from user.models import SearchHistory

logger = logging.getLogger(__name__)


class SearchHistoryException(APIException):
    status_code = 500
    default_detail = 'Đã xảy ra lỗi khi xử lý lịch sử tìm kiếm.'
    default_code = 'search_history_error'


class SearchHistoryController:
    @staticmethod
    def get_user_search_history(user_id: str) -> List[SearchHistory]:
        return SearchHistoryService.get_user_search_history(user_id)

    @staticmethod
    def add_user_search_history(user_id: str, query: str) -> SearchHistory:
        return SearchHistoryService.add_user_search_history(user_id, query)

    @staticmethod
    def delete_search_histories(
            user_id: str,
            queries_to_delete: List[str]) -> int:
        return SearchHistoryService.delete_search_histories(
            user_id, queries_to_delete)
