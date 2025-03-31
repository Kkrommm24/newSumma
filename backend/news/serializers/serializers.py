from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, NewsSummary

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ArticleListSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'url', 'published_at', 'image_url', 'categories']

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(article_id=obj.id).values_list('category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data

class ArticleDetailSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    has_summary = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'content', 'url', 'published_at', 'image_url', 'categories', 'has_summary']

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(article_id=obj.id).values_list('category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data
    
    def get_has_summary(self, obj):
        return NewsSummary.objects.filter(article_id=obj.id).exists()

class SummarySerializer(serializers.ModelSerializer):
    article_title = serializers.SerializerMethodField()

    class Meta:
        model = NewsSummary
        fields = ['id', 'article_id', 'article_title', 'summary_text', 'upvotes', 'downvotes', 'created_at']

    def get_article_title(self, obj):
        try:
            article = NewsArticle.objects.get(id=obj.article_id)
            return article.title
        except NewsArticle.DoesNotExist:
            return None
