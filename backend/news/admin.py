from django.contrib import admin
from .models import User, NewsSource, Category, NewsArticle, NewsArticleCategory, NewsSummary, UserSavedArticle, UserPreference, SummaryFeedback, SearchHistory, Comment, ArticleStats


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active', 'created_at')


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'last_scraped', 'created_at')
    search_fields = ('name', 'website')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_id', 'published_at', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('published_at', 'created_at')


@admin.register(NewsArticleCategory)
class NewsArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ('article_id', 'category_id', 'created_at')
    list_filter = ('created_at',)


@admin.register(NewsSummary)
class NewsSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'article_id', 'upvotes', 'downvotes', 'created_at')
    search_fields = ('summary_text',)
    list_filter = ('created_at',)


@admin.register(UserSavedArticle)
class UserSavedArticleAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'article_id', 'created_at')
    list_filter = ('created_at',)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'created_at')
    list_filter = ('created_at',)


@admin.register(SummaryFeedback)
class SummaryFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'summary_id', 'is_upvote', 'created_at')
    list_filter = ('is_upvote', 'created_at')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'query', 'searched_at')
    search_fields = ('query',)
    list_filter = ('searched_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'article_id', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)


@admin.register(ArticleStats)
class ArticleStatsAdmin(admin.ModelAdmin):
    list_display = (
        'article_id',
        'view_count',
        'comment_count',
        'save_count',
        'created_at')
    list_filter = ('created_at',)
