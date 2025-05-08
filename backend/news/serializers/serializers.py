import os
from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory, NewsSummary, SummaryFeedback, User, Comment
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

DEFAULT_AVATAR_URL = os.getenv('DEFAULT_AVATAR_URL', 'https://example.com/default-avatar.png')

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
    title = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    published_at = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

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
            'user_vote',
            'comment_count'
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

    def get_comment_count(self, obj):
        if obj.article_id:
            return Comment.objects.filter(article_id=obj.article_id).count()
        return 0

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    content = serializers.CharField(max_length=150)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'article_id', 'content', 'created_at', 'updated_at', 'user_id']
        read_only_fields = ['id', 'user', 'article_id', 'created_at', 'updated_at', 'user_id']

    def get_user(self, obj):
        try:
            user = User.objects.get(id=obj.user_id)
            return UserSimpleSerializer(user).data
        except User.DoesNotExist:
            return None

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
        fields = ('id', 'username', 'email', 'avatar', 'is_staff', 'is_superuser')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not representation.get('avatar'):
            representation['avatar'] = DEFAULT_AVATAR_URL
        return representation
