from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, NewsSummary
from recommender.models import SummaryViewLog, SummaryClickLog, SummaryRanking


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class NewsArticleSerializer(serializers.ModelSerializer):
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

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(
            article_id=obj.id).values_list(
            'category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data


class NewsSummarySerializer(serializers.ModelSerializer):
    article = NewsArticleSerializer(read_only=True)
    total_score = serializers.FloatField(read_only=True)

    class Meta:
        model = NewsSummary
        fields = [
            'id',
            'summary_text',
            'upvotes',
            'downvotes',
            'created_at',
            'article',
            'total_score'
        ]


class SummaryViewLogSerializer(serializers.ModelSerializer):
    summary_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsSummary.objects.all(),
        source='summary',
        write_only=True
    )

    class Meta:
        model = SummaryViewLog
        fields = [
            'id',
            'summary_id',
            'summary',
            'duration_seconds',
            'viewed_at'
        ]
        read_only_fields = ['id', 'summary', 'viewed_at']

    def create(self, validated_data):
        return SummaryViewLog.objects.create(**validated_data)


class SummaryClickLogSerializer(serializers.ModelSerializer):
    summary_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsSummary.objects.all(),
        source='summary',
        write_only=True
    )

    class Meta:
        model = SummaryClickLog
        fields = [
            'id',
            'summary_id',
            'summary',
            'clicked_at'
        ]
        read_only_fields = ['id', 'summary', 'clicked_at']

    def create(self, validated_data):
        return SummaryClickLog.objects.create(**validated_data)


class SummaryRankingSerializer(serializers.ModelSerializer):
    summary_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsSummary.objects.all(),
        source='summary',
        write_only=True
    )

    class Meta:
        model = SummaryRanking
        fields = [
            'id',
            'summary_id',
            'summary',
            'category_score',
            'search_history_score',
            'favorite_keywords_score',
            'total_score',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'summary',
            'category_score',
            'search_history_score',
            'favorite_keywords_score',
            'total_score',
            'updated_at'
        ]

    def create(self, validated_data):
        return SummaryRanking.objects.create(**validated_data)
