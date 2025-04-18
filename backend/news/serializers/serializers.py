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

    def c(self, obj):
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
    title = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = NewsSummary
        fields = [
            'id', 
            'article_id', 
            'title',
            'summary_text',
            'image_url',
            'url',
            'upvotes', 
            'downvotes', 
            'created_at'
        ]

    def get_title(self, obj):
        articles = self.context.get('articles', {})
        article = articles.get(str(obj.article_id))
        return article.title if article else None

    def get_image_url(self, obj):
        articles = self.context.get('articles', {})
        article = articles.get(str(obj.article_id))
        return article.image_url if article else None

    def get_url(self, obj):
        articles = self.context.get('articles', {})
        article = articles.get(str(obj.article_id))
        return article.url if article else None
