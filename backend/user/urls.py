from django.urls import path
from user.views.user_preference import UserFavoriteKeywordsView
from user.views.search_history import UserSearchHistoryView
from user.views.bookmark import UserBookmarkView
from .views.user_registration import UserRegistrationView
from .views.password_reset import RequestPasswordResetView, PasswordResetConfirmView
from .views.profile import UserProfileView
from .views.auth_views import PasswordChangeView, AccountDeletionView
from .views.admin_views import (
    AdminDashboardView, AdminCrawlView, AdminSummarizeView,
    AdminUserManagementView, AdminArticleManagementView,
    AdminSummaryManagementView, AdminCommentManagementView,
    AdminFavoriteWordManagementView
)


urlpatterns = [
    path('fav-words/', UserFavoriteKeywordsView.as_view(), name='favourite-words'),
    path('search-history/', UserSearchHistoryView.as_view(), name='search-history'),
    path('bookmarks/', UserBookmarkView.as_view(), name='user-bookmarks'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('delete-account/', AccountDeletionView.as_view(), name='delete-account'),
    
    # Admin URLs
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/crawl/', AdminCrawlView.as_view(), name='admin-crawl'),
    path('admin/summarize/', AdminSummarizeView.as_view(), name='admin-summarize'),
    path('admin/users/', AdminUserManagementView.as_view(), name='admin-users'),
    path('admin/users/<uuid:user_id>/', AdminUserManagementView.as_view(), name='admin-user-detail'),
    path('admin/articles/', AdminArticleManagementView.as_view(), name='admin-articles'),
    path('admin/articles/<uuid:article_id>/', AdminArticleManagementView.as_view(), name='admin-article-detail'),
    path('admin/summaries/', AdminSummaryManagementView.as_view(), name='admin-summaries'),
    path('admin/summaries/<uuid:summary_id>/', AdminSummaryManagementView.as_view(), name='admin-summary-detail'),
    path('admin/comments/', AdminCommentManagementView.as_view(), name='admin-comments'),
    path('admin/comments/<uuid:comment_id>/', AdminCommentManagementView.as_view(), name='admin-comment-detail'),
    path('admin/fav-words/', AdminFavoriteWordManagementView.as_view(), name='admin-fav-words'),
    path('admin/fav-words/<str:keyword>/', AdminFavoriteWordManagementView.as_view(), name='admin-fav-word-detail'),
]
