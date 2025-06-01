import os
from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, Comment, ArticleStats
from summarizer.models import NewsSummary, SummaryFeedback
from user.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

DEFAULT_AVATAR_URL = os.getenv(
    'DEFAULT_AVATAR_URL',
    'https://example.com/default-avatar.png')


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

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(
            article_id=obj.id).values_list(
            'category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance and not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'user',
            'article_id',
            'content',
            'created_at',
            'updated_at')
        read_only_fields = ('id', 'article_id', 'created_at', 'updated_at')

    def get_user(self, obj: Comment):
        if obj.user_id:
            try:
                user_instance = User.objects.get(id=obj.user_id)
                return UserBasicSerializer(user_instance).data
            except User.DoesNotExist:
                return {
                    'id': None,
                    'username': 'Người dùng ẩn danh',
                    'avatar': DEFAULT_AVATAR_URL
                }
        return {
            'id': None,
            'username': 'Người dùng ẩn danh',
            'avatar': DEFAULT_AVATAR_URL
        }

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)
