from rest_framework import generics, permissions
from news.models import NewsArticle, NewsSummary
from news.serializers.serializers import SummarySerializer
from news.services import summary_service


class SummaryDetailView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    queryset = NewsSummary.objects.none()

    def get_object(self):
        summary_id = self.kwargs.get(self.lookup_field)
        summary = summary_service.get_summary_by_id(summary_id)
        return summary

    def get_serializer_context(self):
        context = super().get_serializer_context()
        summary = self.get_object()
        if summary:
            try:
                article = NewsArticle.objects.get(id=summary.article_id)
                context['articles'] = {str(summary.article_id): article}
            except NewsArticle.DoesNotExist:
                context['articles'] = {}
        context['request'] = self.request
        return context


class ArticleSummaryView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'article_id'
    queryset = NewsSummary.objects.none()

    def get_object(self):
        article_id = self.kwargs.get(self.lookup_field)
        summary, article = summary_service.get_latest_summary_by_article_id(
            article_id)
        self.article = article
        return summary

    def get_serializer_context(self):
        context = super().get_serializer_context()
        article = getattr(self, 'article', None)
        if article:
            context['articles'] = {str(article.id): article}
        else:
            context['articles'] = {}
        context['request'] = self.request
        return context
