from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
from user.views.search_history import UserSearchHistoryView


urlpatterns = [
    path('fav-words', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    path('search-history', UserSearchHistoryView.as_view(), name='search-history'),
]
