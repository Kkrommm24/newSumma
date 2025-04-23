from django.core.exceptions import ObjectDoesNotExist
from news.models import UserSavedArticle, NewsArticle, Category, NewsArticleCategory
from rest_framework import status
from rest_framework.exceptions import APIException

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

def add_bookmark(user_id: str, article_id: str):
    if not NewsArticle.objects.filter(id=article_id).exists():
        raise ArticleNotFoundException()

    if UserSavedArticle.objects.filter(user_id=user_id, article_id=article_id).exists():
        raise AlreadyBookmarkedException()

    try:
        UserSavedArticle.objects.create(user_id=user_id, article_id=article_id)
    except Exception as e:
        raise BookmarkException(f"Lỗi khi thêm bookmark: {e}")

def remove_bookmark(user_id: str, article_id: str):
    try:
        bookmark = UserSavedArticle.objects.get(user_id=user_id, article_id=article_id)
        bookmark.delete()
    except ObjectDoesNotExist:
        raise NotBookmarkedException()
    except Exception as e:
        raise BookmarkException(f"Lỗi khi xóa bookmark: {e}")

def get_bookmarks(user_id: str):
    try:
        saved_articles = UserSavedArticle.objects.filter(user_id=user_id)
        return saved_articles
    except Exception as e:
        raise BookmarkException(f"Lỗi khi lấy danh sách bookmark: {e}")
