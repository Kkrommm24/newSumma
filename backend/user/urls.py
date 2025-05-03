from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
from user.views.search_history import UserSearchHistoryView
from user.views.bookmark import UserBookmarkView
from .views.user_registration import UserRegistrationView
from .views.password_reset import RequestPasswordResetView, PasswordResetConfirmView


urlpatterns = [
    path('fav-words', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    path('search-history', UserSearchHistoryView.as_view(), name='search-history'),
    path('bookmarks', UserBookmarkView.as_view(), name='user-bookmarks'),
    path('register', UserRegistrationView.as_view(), name='user-register'),
    path('request-password-reset', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password-reset-confirm', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
