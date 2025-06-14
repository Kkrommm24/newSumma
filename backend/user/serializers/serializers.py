from django.contrib.auth import get_user_model
from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory
from user.models import UserPreference, User, UserSavedArticle, SearchHistory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from user.services import registration_service
from rest_framework.validators import UniqueValidator

User = get_user_model()


def get_password_error_codes(error_list):
    """Trích xuất mã lỗi từ danh sách lỗi của Django."""
    error_codes = []
    for error in error_list:
        if hasattr(error, 'code'):
            error_codes.append(error.code)
    return error_codes


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
        cleaned_keywords = [
            kw.strip() for kw in value if isinstance(
                kw, str) and kw.strip()]
        if not cleaned_keywords:
            raise serializers.ValidationError(
                "Danh sách từ khóa không hợp lệ.")
        return cleaned_keywords


class DeleteFavoriteKeywordsSerializer(serializers.Serializer):
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=False),
        allow_empty=False,
        help_text="Danh sách các từ khóa cần xóa."
    )

    def validate_keywords(self, value):
        cleaned_keywords = [
            kw for kw in value if isinstance(
                kw, str) and kw.strip()]
        if not cleaned_keywords:
            raise serializers.ValidationError(
                "Danh sách từ khóa cần xóa không được rỗng.")
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
    query = serializers.CharField(
        max_length=255,
        required=True,
        allow_blank=False)

    def validate_query(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Query cannot be empty or just whitespace.")
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
    password = serializers.CharField(
        write_only=True, required=True, style={
            'input_type': 'password'})
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm password"),
        style={
            'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message='error_email_exists'
                    )
                ]
            },
            'username': {
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message='error_username_exists'
                    )
                ]
            }
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password2": ['password_mismatch']})
        try:
            validate_password(data['password'], user=None)
        except DjangoValidationError as e:
            error_codes = get_password_error_codes(e.error_list)
            raise serializers.ValidationError({"password": error_codes})
        return data

    def create(self, validated_data):
        try:
            user = registration_service.register_user(validated_data.copy())
            return user
        except Exception as e:
            raise serializers.ValidationError(str(e))


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # Không validate email tồn tại để tránh tiết lộ thông tin
        return value


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True, required=True, style={
            'input_type': 'password'})
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm password"),
        style={
            'input_type': 'password'})
    reset_token = serializers.CharField(required=True)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password2": ['password_mismatch']})
        try:
            validate_password(data['password'], user=None)
        except DjangoValidationError as e:
            error_codes = get_password_error_codes(e.error_list)
            raise serializers.ValidationError({"password": error_codes})
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']
        extra_kwargs = {
            'email': {
                'required': False,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message='error_email_exists'
                    )
                ]
            },
            'username': {
                'required': False,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message='error_username_exists'
                    )
                ]
            }
        }

    def validate_username(self, value):
        if self.instance and User.objects.filter(
                username=value).exclude(
                pk=self.instance.pk).exists():
            raise serializers.ValidationError('error_username_exists')
        return value

    def validate_email(self, value):
        if self.instance and User.objects.filter(
                email=value).exclude(
                pk=self.instance.pk).exists():
            raise serializers.ValidationError('error_email_exists')
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, label=_("Confirm new password"))

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('error_old_password_incorrect')
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(get_password_error_codes(e.error_list))
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                {'new_password_confirm': ['password_mismatch']})
        return data


class AccountDeletionSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('error_password_incorrect')
        return value
