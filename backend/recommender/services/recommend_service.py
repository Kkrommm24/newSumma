from recommender.recommenders.recommender import decide_recommendation_strategy
from news.models import NewsArticle, NewsSummary, UserPreference, SearchHistory
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
import logging
from functools import reduce
import operator
from django.utils import timezone
import datetime
from news.utils.summary_utils import get_latest_summaries, get_articles_for_summaries

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5
MIN_RANK_THRESHOLD = 0.05

def _get_user_favorite_keywords(user_id):
    try:
        user_pref = UserPreference.objects.get(user_id=user_id)
        return user_pref.favorite_keywords or []
    except UserPreference.DoesNotExist:
        return []

def _get_user_search_history_keywords(user_id):
    try:
        recent_searches = SearchHistory.objects.filter(user_id=user_id).order_by('-searched_at').values_list('query', flat=True)[:SEARCH_HISTORY_LIMIT]
        queries = list(recent_searches)
        logger.debug(f"Raw history queries for user {user_id} (ordered desc): {queries}")
        return queries
    except Exception as e:
        logger.error(f"Lỗi khi lấy SearchHistory (ordered) cho user {user_id} trong service: {e}")
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

        summaries_above_threshold = list(NewsSummary.objects.annotate(
            rank=SearchRank(SearchVector('summary_text', config=search_config), combined_query)
        ).filter(
            search_vector=combined_query,
            rank__gte=MIN_RANK_THRESHOLD
        ))

        if not summaries_above_threshold:
            logger.info(f"[FTS DEBUG] Keywords: '{keywords}', Found: 0 summaries above rank {MIN_RANK_THRESHOLD}")
            return []

        article_ids = [s.article_id for s in summaries_above_threshold]
        articles_data = NewsArticle.objects.filter(id__in=article_ids).values('id', 'published_at')
        min_datetime = timezone.make_aware(datetime.datetime.min, datetime.timezone.utc)
        publish_dates = {
            str(a['id']): a['published_at'] if a['published_at'] else min_datetime
            for a in articles_data
        }

        def sort_key(summary):
            pub_date = publish_dates.get(str(summary.article_id), min_datetime)
            return (pub_date, summary.rank)

        sorted_summaries = sorted(summaries_above_threshold, key=sort_key, reverse=True)

        logger.info(f"[FTS DEBUG] Keywords: '{keywords}', Type: 'plain', Config: '{search_config}', Found: {len(sorted_summaries)} summaries (Filtered rank >= {MIN_RANK_THRESHOLD}, Sorted by pub_date DESC, rank DESC)")

        return sorted_summaries

    except Exception as e:
        logger.error(f"Lỗi khi thực hiện full-text search (rank filter, Python sort pub_date prio) cho keywords '{keywords}' (config: {search_config}) trong service: {e}")
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
