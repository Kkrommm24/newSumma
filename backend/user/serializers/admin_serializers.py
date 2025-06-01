from rest_framework import serializers
from news.models import NewsArticle, NewsSource, Comment
from summarizer.models import NewsSummary
from user.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'is_staff',
            'is_active',
            'created_at',
            'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class AdminArticleSerializer(serializers.ModelSerializer):
    source_name = serializers.SerializerMethodField()
    has_summary = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = (
            'id',
            'title',
            'content',
            'url',
            'source_id',
            'source_name',
            'published_at',
            'image_url',
            'created_at',
            'updated_at',
            'has_summary')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_source_name(self, obj):
        try:
            source = NewsSource.objects.get(id=obj.source_id)
            return source.name
        except NewsSource.DoesNotExist:
            return None

    def get_has_summary(self, obj):
        try:
            return NewsSummary.objects.filter(article_id=obj.id).exists()
        except Exception:
            return False


class AdminSummarySerializer(serializers.ModelSerializer):
    article_title = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = NewsSummary
        fields = (
            'id',
            'article_id',
            'article_title',
            'summary_text',
            'upvotes',
            'downvotes',
            'created_at',
            'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_article_title(self, obj):
        try:
            article = NewsArticle.objects.get(id=obj.article_id)
            return article.title
        except NewsArticle.DoesNotExist:
            return None


class AdminCommentSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    article_title = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'user_id',
            'username',
            'article_id',
            'article_title',
            'content',
            'created_at',
            'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_username(self, obj):
        try:
            user = User.objects.get(id=obj.user_id)
            return user.username
        except User.DoesNotExist:
            return None

    def get_article_title(self, obj):
        try:
            article = NewsArticle.objects.get(id=obj.article_id)
            return article.title
        except NewsArticle.DoesNotExist:
            return None


class AdminFavoriteWordSerializer(serializers.Serializer):
    keyword = serializers.CharField()
    user_count = serializers.IntegerField()
