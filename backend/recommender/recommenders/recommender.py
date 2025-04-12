from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from news.models import UserPreference, NewsSummary, SearchHistory
import logging

logger = logging.getLogger(__name__)

SEARCH_HISTORY_LIMIT = 5

def decide_recommendation_strategy(user_id, get_fav_keywords_func, get_history_keywords_func, find_summaries_func, get_latest_func):
    keywords_to_use = []
    source_type = 'latest'
    source_keywords = []
    
    fav_keywords = get_fav_keywords_func(user_id)
    hist_keywords = get_history_keywords_func(user_id)

    if fav_keywords:
        keywords_to_use = fav_keywords
        source_type = 'favorite'
        source_keywords = fav_keywords
        logger.info(f"Recommender: Trying favorite keywords: {keywords_to_use}")
    elif hist_keywords:
        keywords_to_use = hist_keywords
        source_type = 'history'
        source_keywords = hist_keywords
        logger.info(f"Recommender: Trying history keywords: {keywords_to_use}")
    else:
        logger.info(f"Recommender: No keywords found, will use latest only.")

    fts_summaries = []
    if keywords_to_use:
        fts_summaries = find_summaries_func(keywords_to_use)
        for summary in fts_summaries:
            summary.source_keywords = source_keywords

    latest_summaries = get_latest_func()
    for summary in latest_summaries:
        summary.source_keywords = []
    
    final_summaries = []
    seen_summary_ids = set()

    for summary in fts_summaries:
        if summary.id not in seen_summary_ids:
            final_summaries.append(summary)
            seen_summary_ids.add(summary.id)

    for summary in latest_summaries:
        if summary.id not in seen_summary_ids:
            final_summaries.append(summary)
            seen_summary_ids.add(summary.id)

    source_info = {'type': source_type, 'keywords': source_keywords, 'fts_count': len(fts_summaries), 'final_count': len(final_summaries)}
    logger.info(f"Recommender for user {user_id}: {source_info}")

    return final_summaries, source_info
