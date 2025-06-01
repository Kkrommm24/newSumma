import logging
from django.db.models import Q, F, Case, When, Value, IntegerField
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from summarizer.models import NewsSummary

logger = logging.getLogger(__name__)


def search_summaries_with_articles(query_string):
    try:
        search_query = SearchQuery(
            query_string,
            config='vietnamese',
            search_type='websearch')
        vector = SearchVector('summary_text', config='vietnamese')

        summary_queryset = NewsSummary.objects.annotate(
            exact_match_boost=Case(
                When(summary_text__icontains=query_string, then=Value(1)),
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

        return summary_queryset

    except Exception as e:
        logger.error(
            f"Error during summary search service for query '{query_string}': {e}",
            exc_info=True)
        # Có thể raise lỗi cụ thể hơn hoặc trả về None tùy cách xử lý ở view
        return None
