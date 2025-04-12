from recommender.recommenders.recommender import decide_recommendation_strategy
from news.serializers.serializers import SummarySerializer
from news.models import NewsArticle, NewsSummary, UserPreference, SearchHistory
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
import logging
from functools import reduce
import operator
from django.utils import timezone
import datetime
from summarizer.utils.summary_utils import get_latest_summaries, get_articles_for_summaries

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5

def _get_user_favorite_keywords(user_id):
    try:
        user_pref = UserPreference.objects.get(user_id=user_id)
        return user_pref.favorite_keywords or []
    except UserPreference.DoesNotExist:
        return []

def _get_user_search_history_keywords(user_id):
    try:
        recent_searches = SearchHistory.objects.filter(user_id=user_id).order_by('-searched_at').values_list('query', flat=True).distinct()[:SEARCH_HISTORY_LIMIT]
        return list(recent_searches)
    except Exception as e:
        logger.error(f"Lỗi khi lấy SearchHistory cho user {user_id} trong service: {e}")
        return []

def _find_summaries_by_keywords(keywords):
    if not keywords:
        return []
    try:
        search_config = 'vietnamese'
        search_queries = [SearchQuery(kw, search_type='plain', config=search_config) for kw in keywords]
        if not search_queries:
            return []
        combined_query = reduce(operator.or_, search_queries)

        ranked_summaries = list(NewsSummary.objects.annotate(
            rank=SearchRank(SearchVector('summary_text', config=search_config), combined_query)
        ).filter(
            search_vector=combined_query
        ).order_by('-rank'))

        if not ranked_summaries:
            logger.info(f"[FTS DEBUG] Keywords: '{keywords}', Found: 0 summaries")
            return []

        article_ids = [s.article_id for s in ranked_summaries]
        articles_data = NewsArticle.objects.filter(id__in=article_ids).values('id', 'published_at')
        min_datetime = timezone.make_aware(datetime.datetime.min, datetime.timezone.utc)
        publish_dates = { 
            str(a['id']): a['published_at'] if a['published_at'] else min_datetime
            for a in articles_data
        }

        def sort_key(summary):
            pub_date = publish_dates.get(str(summary.article_id), min_datetime)
            return (summary.rank, pub_date)
            
        sorted_summaries = sorted(ranked_summaries, key=sort_key, reverse=True)

        logger.info(f"[FTS DEBUG] Keywords: '{keywords}', Type: 'plain' (Combined OR), Config: '{search_config}', Found: {len(sorted_summaries)} summaries (Sorted by overall rank & pub_date)")

        return sorted_summaries

    except Exception as e:
        logger.error(f"Lỗi khi thực hiện full-text search (combined OR, Python sort) cho keywords '{keywords}' (config: {search_config}) trong service: {e}")
        return []

def get_recommendations_for_user(user_id):
    try:
        combined_summaries, source_info = decide_recommendation_strategy(
            user_id,
            get_fav_keywords_func=_get_user_favorite_keywords,
            get_history_keywords_func=_get_user_search_history_keywords,
            find_summaries_func=_find_summaries_by_keywords,
            get_latest_func=get_latest_summaries 
        )

        if not combined_summaries:
            logger.info(f"Không có gợi ý nào được trả về cho user {user_id} từ recommender. Source: {source_info}")
            return [], {}, source_info

        articles_dict = get_articles_for_summaries(combined_summaries)

        if not articles_dict and combined_summaries:
            logger.warning(f"Không tìm thấy article nào cho các summary gợi ý (kết hợp) của user {user_id}.")

        return combined_summaries, articles_dict, source_info

    except Exception as e:
        logger.exception(f"❌ Lỗi không mong muốn trong get_recommendations_for_user cho user {user_id}: {e}")
        return [], {}, {'type': 'error', 'message': str(e)}
