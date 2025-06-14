from django.core.exceptions import ObjectDoesNotExist
from news.models import NewsArticle, ArticleStats
from user.models import UserSavedArticle
from rest_framework import status
from rest_framework.exceptions import APIException
from django.db.models import F
from user.services.bookmark_service import BookmarkService


class BookmarkException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Đã xảy ra lỗi khi xử lý bookmark.'
    default_code = 'bookmark_error'


class ArticleNotFoundException(BookmarkException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Bài viết không tồn tại.'
    default_code = 'article_not_found'


class AlreadyBookmarkedException(BookmarkException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Bài viết đã được bookmark.'
    default_code = 'already_bookmarked'


class NotBookmarkedException(BookmarkException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Bài viết chưa được bookmark.'
    default_code = 'not_bookmarked'


class BookmarkController:
    @staticmethod
    def add_bookmark(user_id: str, article_id: str):
        if not BookmarkService.check_article_exists(article_id):
            raise ArticleNotFoundException()

        if BookmarkService.check_bookmark_exists(user_id, article_id):
            raise AlreadyBookmarkedException()

        try:
            BookmarkService.create_bookmark(user_id, article_id)
            BookmarkService.update_article_stats(article_id)
        except Exception as e:
            raise BookmarkException(f"Lỗi khi thêm bookmark: {e}")

    @staticmethod
    def remove_bookmark(user_id: str, article_id: str):
        try:
            bookmark = BookmarkService.get_bookmark(user_id, article_id)
            BookmarkService.delete_bookmark(bookmark)
            BookmarkService.decrease_article_stats(article_id)
        except ObjectDoesNotExist:
            raise NotBookmarkedException()
        except Exception as e:
            raise BookmarkException(f"Lỗi khi xóa bookmark: {e}")

    @staticmethod
    def get_bookmarks(user_id: str):
        try:
            return BookmarkService.get_user_bookmarks(user_id)
        except Exception as e:
            raise BookmarkException(f"Lỗi khi lấy danh sách bookmark: {e}")
