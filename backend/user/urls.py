from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
from user.views.search_history import UserSearchHistoryView
from user.views.bookmark import UserBookmarkView
from .views.user_registration import UserRegistrationView
from .views.password_reset import RequestPasswordResetView, PasswordResetConfirmView
from .views.profile import UserProfileView
from .views.auth_views import PasswordChangeView, AccountDeletionView


urlpatterns = [
    path('fav-words/', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    path('search-history/', UserSearchHistoryView.as_view(), name='search-history'),
    path('bookmarks/', UserBookmarkView.as_view(), name='user-bookmarks'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('request-password-reset', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('delete-account/', AccountDeletionView.as_view(), name='delete-account'),
]
