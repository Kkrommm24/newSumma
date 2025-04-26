from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
from user.views.search_history import UserSearchHistoryView
from user.views.bookmark import UserBookmarkView
from .views.user_view import UserRegistrationView


urlpatterns = [
    path('fav-words', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    path('search-history', UserSearchHistoryView.as_view(), name='search-history'),
    path('bookmarks', UserBookmarkView.as_view(), name='user-bookmarks'),
    path('register', UserRegistrationView.as_view(), name='user-register'),
]
