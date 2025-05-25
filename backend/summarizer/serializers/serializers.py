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
        fields = [
            'id',
            'title',
            'url',
            'published_at',
            'image_url',
            'categories']

    def c(self, obj):
        category_ids = NewsArticleCategory.objects.filter(
            article_id=obj.id).values_list(
            'category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data
