from django.contrib.auth import get_user_model
from rest_framework import serializers
from news.models import NewsArticle, Category, NewsArticleCategory
from user.models import UserPreference, User, UserSavedArticle, SearchHistory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password, MinimumLengthValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from user.services import registration_service 

User = get_user_model()

# Từ điển dịch lỗi mật khẩu
PASSWORD_ERROR_TRANSLATIONS = {
    "This password is too common.": _("Mật khẩu này quá phổ biến."),
    "The password is too similar to the username.": _("Mật khẩu quá giống với tên người dùng."),
    "The password is too similar to the email address.": _("Mật khẩu quá giống với địa chỉ email."),
}


def translate_password_errors(error_list):
    translated_errors = []
    for error in error_list:
        error_code = getattr(error, 'code', None)  # Lấy code một cách an toàn

        if error_code == 'password_too_short':
            min_length = MinimumLengthValidator().min_length  # Lấy cấu hình min_length
            translated_errors.append(
                _(f"Mật khẩu phải chứa ít nhất {min_length} ký tự."))
        elif error_code == 'password_too_common':
            translated_errors.append(
                PASSWORD_ERROR_TRANSLATIONS.get(
                    error.message,
                    _("Mật khẩu này quá phổ biến.")))
        elif error_code == 'password_entirely_numeric':
            translated_errors.append(
                _("Mật khẩu không được hoàn toàn là chữ số."))
        elif error_code == 'password_too_similar':
            # Dùng thông điệp từ điển nếu có, hoặc lỗi gốc
            translated_errors.append(
                PASSWORD_ERROR_TRANSLATIONS.get(
                    error.message, str(error)))
        else:
            translated_errors.append(
                PASSWORD_ERROR_TRANSLATIONS.get(
                    error.message, str(error)))
    return translated_errors


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
            'email': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                _("An active user with that email already exists."))
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError(
                _("An active user with that username already exists."))
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password2": _("Mật khẩu xác nhận không khớp.")})
        try:
            # Sử dụng user=None vì user chưa được tạo
            validate_password(data['password'], user=None)
        except DjangoValidationError as e:
            translated_errors = translate_password_errors(e.error_list)
            raise serializers.ValidationError({"password": translated_errors})
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
                {"password2": _("Mật khẩu xác nhận không khớp.")})
        try:
            # Tương tự, kiểm tra với user=None
            validate_password(data['password'], user=None)
        except DjangoValidationError as e:
            translated_errors = translate_password_errors(e.error_list)
            raise serializers.ValidationError({"password": translated_errors})
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
        }

    def validate_username(self, value):
        if self.instance and User.objects.filter(
                username=value).exclude(
                pk=self.instance.pk).exists():
            raise serializers.ValidationError("Username này đã được sử dụng.")
        return value

    def validate_email(self, value):
        if self.instance and User.objects.filter(
                email=value).exclude(
                pk=self.instance.pk).exists():
            raise serializers.ValidationError("Email này đã được sử dụng.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(
        required=True, write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context.get('request').user)
        except DjangoValidationError as e:
            translated_errors = translate_password_errors(e.error_list)
            raise serializers.ValidationError(translated_errors)
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Mật khẩu mới không khớp.")})
        return data


class AccountDeletionSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=True, write_only=True, style={
            'input_type': 'password'})
