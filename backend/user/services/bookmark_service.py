from django.core.exceptions import ObjectDoesNotExist
from news.models import NewsArticle, ArticleStats
from user.models import UserSavedArticle
from rest_framework import status
from rest_framework.exceptions import APIException
from django.db.models import F
from typing import List


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


class BookmarkService:
    @staticmethod
    def check_article_exists(article_id: str) -> bool:
        return NewsArticle.objects.filter(id=article_id).exists()

    @staticmethod
    def check_bookmark_exists(user_id: str, article_id: str) -> bool:
        return UserSavedArticle.objects.filter(
            user_id=user_id,
            article_id=article_id).exists()

    @staticmethod
    def create_bookmark(user_id: str, article_id: str) -> UserSavedArticle:
        return UserSavedArticle.objects.create(
            user_id=user_id, article_id=article_id)

    @staticmethod
    def update_article_stats(article_id: str):
        stats, created = ArticleStats.objects.get_or_create(
            article_id=article_id,
            defaults={'save_count': 1}
        )
        if not created:
            ArticleStats.objects.filter(
                article_id=article_id).update(
                save_count=F('save_count') + 1)

    @staticmethod
    def get_bookmark(user_id: str, article_id: str) -> UserSavedArticle:
        return UserSavedArticle.objects.get(
            user_id=user_id, article_id=article_id)

    @staticmethod
    def delete_bookmark(bookmark: UserSavedArticle):
        bookmark.delete()

    @staticmethod
    def decrease_article_stats(article_id: str):
        ArticleStats.objects.filter(
            article_id=article_id).update(
            save_count=F('save_count') - 1)

    @staticmethod
    def get_user_bookmarks(user_id: str) -> List[UserSavedArticle]:
        return UserSavedArticle.objects.filter(user_id=user_id)


def add_bookmark(user_id: str, article_id: str):
    if not NewsArticle.objects.filter(id=article_id).exists():
        raise ArticleNotFoundException()

    if UserSavedArticle.objects.filter(
            user_id=user_id,
            article_id=article_id).exists():
        raise AlreadyBookmarkedException()

    try:
        UserSavedArticle.objects.create(user_id=user_id, article_id=article_id)
        stats, created = ArticleStats.objects.get_or_create(
            article_id=article_id,
            defaults={'save_count': 1}
        )
        if not created:
            ArticleStats.objects.filter(
                article_id=article_id).update(
                save_count=F('save_count') + 1)

    except Exception as e:
        raise BookmarkException(f"Lỗi khi thêm bookmark: {e}")


def remove_bookmark(user_id: str, article_id: str):
    try:
        bookmark = UserSavedArticle.objects.get(
            user_id=user_id, article_id=article_id)
        bookmark.delete()
        ArticleStats.objects.filter(
            article_id=article_id).update(
            save_count=F('save_count') - 1)

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
