from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
# from user.views.search_history import get_search_history, register_search_history, delete_search_history


urlpatterns = [
    path('fav-words', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    # path('fav-words/delete/', delete_favourite_words, name='delete-favourite-words'),
    # path('search-history/list', get_search_history, name='get-search-history'),
    # path('search-history/register/', register_search_history, name='register-search-history'),
    # path('search-history/delete/', delete_search_history, name='delete-search-history')
]
