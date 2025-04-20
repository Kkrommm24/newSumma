from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, NewsSummary, SummaryFeedback

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

class SummarySerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    published_at = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = NewsSummary
        fields = [
            'id', 
            'article_id', 
            'title',
            'summary_text',
            'image_url',
            'url',
            'keywords',
            'published_at',
            'upvotes', 
            'downvotes', 
            'created_at',
            'user_vote'
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

    def get_published_at(self, obj):
        articles = self.context.get('articles', {})
        article = articles.get(str(obj.article_id))
        return article.published_at if article else None

    def get_keywords(self, obj):
        return getattr(obj, 'source_keywords', [])

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                feedback = SummaryFeedback.objects.get(summary_id=obj.id, user_id=request.user.id)
                return feedback.is_upvote
            except SummaryFeedback.DoesNotExist:
                return None
            except Exception as e:
                return None
        return None
