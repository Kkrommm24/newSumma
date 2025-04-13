# backend/summarizer/views/search.py
import logging
from django.db.models import Q, F, Case, When, Value, IntegerField
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from news.models import NewsSummary, NewsArticle
from summarizer.serializers.serializers import SummarySerializer
from news.utils.pagination import InfiniteScrollPagination

logger = logging.getLogger(__name__)

class ArticleSummarySearchView(APIView):
    permission_classes = [AllowAny]
    pagination_class = InfiniteScrollPagination

    def get(self, request, *args, **kwargs):
        query_param = request.query_params.get('q', None)

        if not query_param or not query_param.strip():
            return Response(
                {"error": "Search query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        query = query_param.strip()

        search_query = SearchQuery(query, config='vietnamese', search_type='websearch')
        vector = SearchVector('summary_text', config='vietnamese')

        try:
            queryset = NewsSummary.objects.annotate(
                exact_match_boost=Case(
                    When(summary_text__icontains=query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ),
                rank=SearchRank(F('search_vector'), search_query)
            ).filter(
                search_vector=search_query
            ).order_by(
                '-exact_match_boost',
                '-rank',
                '-created_at'
            )

            paginator = self.pagination_class()
            paginated_summaries = paginator.paginate_queryset(queryset, request, view=self)

            articles_dict = {}
            if paginated_summaries:
                article_ids = {summary.article_id for summary in paginated_summaries}
                articles_queryset = NewsArticle.objects.filter(id__in=article_ids)
                articles_dict = {str(article.id): article for article in articles_queryset}

            serializer_context = {'articles': articles_dict}
            serializer = SummarySerializer(paginated_summaries, many=True, context=serializer_context)

            count = paginator.page.paginator.count if hasattr(paginator, 'page') else queryset.count()
            logger.info(f"Found {count} summary results for query: {query}")
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Error during article summary search for query '{query}': {e}", exc_info=True)
            return Response(
                {"error": "An error occurred during search."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )