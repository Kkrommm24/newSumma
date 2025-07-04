# backend/summarizer/views/search.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from news.models import NewsArticle
from summarizer.serializers.serializers import SummarySerializer
from news.utils.pagination import StandardResultsSetPagination
from summarizer.summarizers.search_controller import search_controller

logger = logging.getLogger(__name__)


class ArticleSummarySearchView(APIView):
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        query_param = request.query_params.get('q', None)

        if not query_param or not query_param.strip():
            return Response(
                {"error": "Search query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        query = query_param.strip()

        try:
            summary_queryset = search_controller.search_summaries_interface(
                query)

            paginator = self.pagination_class()
            paginated_summaries = paginator.paginate_queryset(
                summary_queryset, request, view=self)

            articles_dict = {}
            if paginated_summaries:
                article_ids = {
                    summary.article_id for summary in paginated_summaries}
                articles_queryset = NewsArticle.objects.filter(
                    id__in=article_ids)
                articles_dict = {
                    str(article.id): article for article in articles_queryset}

            serializer_context = {'articles': articles_dict}
            serializer = SummarySerializer(
                paginated_summaries, many=True, context=serializer_context)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(
                f"SearchView: Error during search for query '{query}': {e}",
                exc_info=False)
            return Response(
                {"error": "An error occurred during search processing."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
