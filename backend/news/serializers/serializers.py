import os
from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, NewsSummary, SummaryFeedback, User, Comment, ArticleStats
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


class ArticleDetailSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    has_summary = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = [
            'id',
            'title',
            'content',
            'url',
            'published_at',
            'image_url',
            'categories',
            'has_summary']

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(
            article_id=obj.id).values_list(
            'category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        return CategorySerializer(categories, many=True).data

    def get_has_summary(self, obj):
        return NewsSummary.objects.filter(article_id=obj.id).exists()


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance and not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation


class CategoryBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ArticleForSummarySerializer(serializers.ModelSerializer):
    categories = CategoryBasicSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = (
            'id',
            'title',
            'url',
            'published_at',
            'image_url',
            'categories'
        )
        read_only_fields = fields


class SummarySerializer(serializers.ModelSerializer):
    article = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = NewsSummary
        fields = (
            'id',
            'article_id',
            'article',
            'summary_text',
            'upvotes',
            'downvotes',
            'created_at',
            'updated_at',
            'user_vote',
            'comment_count',
        )

    def get_article(self, obj: NewsSummary):
        articles_dict = self.context.get('articles', {})
        article_instance = articles_dict.get(str(obj.article_id))

        if article_instance:
            return ArticleForSummarySerializer(
                article_instance, context=self.context).data

        return None

    def get_user_vote(self, obj: NewsSummary):
        request = self.context.get('request')
        if request and hasattr(request,
                               'user') and request.user.is_authenticated:
            try:
                feedback = SummaryFeedback.objects.get(
                    summary_id=obj.id, user_id=request.user.id)
                return feedback.is_upvote
            except SummaryFeedback.DoesNotExist:
                return None
        return None

    def get_comment_count(self, obj: NewsSummary):
        try:
            article_stats = ArticleStats.objects.get(article_id=obj.article_id)
            return article_stats.comment_count
        except ArticleStats.DoesNotExist:
            return 0


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


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance and not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    pass

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'avatar',
            'is_staff',
            'is_superuser')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance and not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation
