from rest_framework import generics, permissions
from news.models import NewsArticle
from summarizer.models import NewsSummary
from summarizer.serializers.serializers import SummarySerializer
from summarizer.summarizers.summay_detail_controller import summary_detail_controller
import logging

logger = logging.getLogger(__name__)


class SummaryDetailView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    queryset = NewsSummary.objects.all()

    def get_object(self):
        summary_id = self.kwargs.get(self.lookup_field)
        try:
            summary = summary_detail_controller.get_summary_detail_interface(summary_id)
            return summary
        except Exception as e:
            logger.error(f"SummaryDetailView: Error getting object for summary_id {summary_id}: {e}", exc_info=True)
            raise

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            summary = self.get_object()
            if summary and summary.article_id:
                try:
                    article = NewsArticle.objects.get(id=summary.article_id)
                    context['articles'] = {str(summary.article_id): article}
                except NewsArticle.DoesNotExist:
                    logger.warning(f"SummaryDetailView: Article {summary.article_id} not found for summary {summary.id}")
                    context['articles'] = {}
            else:
                context['articles'] = {}
        except Exception:
            context['articles'] = {}
            pass
        context['request'] = self.request
        return context


class ArticleSummaryView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'article_id'
    queryset = NewsSummary.objects.all()

    def get_object(self):
        article_id = self.kwargs.get(self.lookup_field)
        try:
            summary, article = summary_detail_controller.get_article_summary_interface(article_id)
            self.article = article
            return summary
        except Exception as e:
            logger.error(f"ArticleSummaryView: Error getting object for article_id {article_id}: {e}", exc_info=True)
            raise

    def get_serializer_context(self):
        context = super().get_serializer_context()
        article = getattr(self, 'article', None)
        if article:
            context['articles'] = {str(article.id): article}
        else:
            context['articles'] = {}
        context['request'] = self.request
        return context
