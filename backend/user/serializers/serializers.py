from rest_framework import serializers
from news.models import UserPreference, SearchHistory

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
