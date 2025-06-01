from rest_framework import serializers
from news.models import ArticleStats, NewsArticle, Category, NewsArticleCategory
from summarizer.models import NewsSummary, SummaryFeedback


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
