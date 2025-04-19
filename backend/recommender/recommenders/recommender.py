import logging

logger = logging.getLogger(__name__)

SEARCH_HISTORY_LIMIT = 5

def decide_recommendation_strategy(user_id, get_fav_keywords_func, get_history_keywords_func, find_summaries_func, get_latest_func):
    fav_keywords = get_fav_keywords_func(user_id)
    ordered_hist_queries = get_history_keywords_func(user_id)

    hist_fts_summaries = []
    seen_summary_ids = set()
    processed_hist_queries = set()

    if ordered_hist_queries:
        for query in ordered_hist_queries:
            if query in processed_hist_queries:
                continue
            processed_hist_queries.add(query)
            current_hist_summaries = find_summaries_func([query]) 
            
            for summary in current_hist_summaries:
                if summary.id not in seen_summary_ids:
                    summary.source_type = 'history' 
                    summary.source_keywords = [query]
                    hist_fts_summaries.append(summary)
                    seen_summary_ids.add(summary.id)

    fav_fts_summaries = []
    if fav_keywords:
        current_fav_summaries = find_summaries_func(fav_keywords)
        for summary in current_fav_summaries:
            if summary.id not in seen_summary_ids:
                summary.source_type = 'favorite'
                summary.source_keywords = fav_keywords
                fav_fts_summaries.append(summary)

    latest_summaries = get_latest_func()
    for summary in latest_summaries:
        summary.source_type = 'latest'
        summary.source_keywords = []

    final_summaries = []
    final_summaries.extend(hist_fts_summaries)

    for summary in fav_fts_summaries:
        if summary.id not in seen_summary_ids:
            final_summaries.append(summary)
            seen_summary_ids.add(summary.id)

    for summary in latest_summaries:
        if summary.id not in seen_summary_ids:
            summary.source_type = 'latest'
            summary.source_keywords = []
            final_summaries.append(summary)
            seen_summary_ids.add(summary.id)

    primary_source_type = 'latest'
    primary_keywords = []
    if hist_fts_summaries:
        primary_source_type = 'history'
        primary_keywords = list(processed_hist_queries)
    elif fav_fts_summaries:
        primary_source_type = 'favorite'
        primary_keywords = fav_keywords

    source_info = {
        'primary_source': primary_source_type,
        'primary_keywords': primary_keywords,
        'history_queries_tried': list(processed_hist_queries),
        'favorite_keywords': fav_keywords,
        'history_found_count': len(hist_fts_summaries),
        'favorite_found_count': len(fav_fts_summaries),
        'final_count': len(final_summaries)
    }

    return final_summaries, source_info
