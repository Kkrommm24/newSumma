from django.contrib.auth import get_user_model
from rest_framework import serializers
from news.models import UserPreference, SearchHistory, UserSavedArticle, NewsArticle, Category, NewsArticleCategory
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['favorite_keywords']
        read_only_fields = ['favorite_keywords'] 
        
class AddFavoriteKeywordsSerializer(serializers.Serializer):
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=False),
        allow_empty=False,
        help_text="Danh sách các từ khóa cần thêm."
    )

    def validate_keywords(self, value):
        cleaned_keywords = [kw.strip() for kw in value if isinstance(kw, str) and kw.strip()]
        if not cleaned_keywords:
            raise serializers.ValidationError("Danh sách từ khóa không hợp lệ.")
        return cleaned_keywords

class DeleteFavoriteKeywordsSerializer(serializers.Serializer):
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=False),
        allow_empty=False,
        help_text="Danh sách các từ khóa cần xóa."
    )

    def validate_keywords(self, value):
        cleaned_keywords = [kw for kw in value if isinstance(kw, str) and kw.strip()]
        if not cleaned_keywords:
             raise serializers.ValidationError("Danh sách từ khóa cần xóa không được rỗng.")
        return value
    
class UserSearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ('id', 'query', 'searched_at')

class DeleteSearchHistorySerializer(serializers.Serializer):
    queries = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False
    )

class AddSearchHistorySerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255, required=True, allow_blank=False)

    def validate_query(self, value):
        if not value.strip():
            raise serializers.ValidationError("Query cannot be empty or just whitespace.")
        return value.strip()

class AddBookmarkSerializer(serializers.Serializer):
    article_id = serializers.UUIDField(required=True)

    def validate_article_id(self, value):
        if not NewsArticle.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bài viết không tồn tại.")
        return value

class DeleteBookmarkSerializer(serializers.Serializer):
    article_id = serializers.UUIDField(required=True)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class BookmarkedArticleSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'url', 'published_at', 'image_url', 'categories']

    def get_categories(self, obj):
        category_ids = NewsArticleCategory.objects.filter(article_id=obj.id).values_list('category_id', flat=True)
        categories = Category.objects.filter(id__in=category_ids)
        
        return CategorySerializer(categories, many=True).data
    

class UserBookmarkSerializer(serializers.ModelSerializer):
    article = serializers.SerializerMethodField()

    class Meta:
        model = UserSavedArticle
        fields = ['article']

    def get_article(self, obj):
        try:
            article = NewsArticle.objects.get(id=obj.article_id)
            return BookmarkedArticleSerializer(article).data
        except NewsArticle.DoesNotExist:
            return None
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label=_("Confirm password"), style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
        return value
        
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("A user with that username already exists."))
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": _("Password fields didn't match.")})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user 

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Không tìm thấy người dùng với địa chỉ email này."))
        return value

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label=_("Confirm password"), style={'input_type': 'password'})
    reset_token = serializers.CharField(required=True)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": _("Mật khẩu xác nhận không khớp.")})
        return data 
