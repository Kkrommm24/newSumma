from news.models import NewsArticle, NewsArticleCategory, ArticleStats
from user.models import UserPreference
from summarizer.models import NewsSummary, SummaryFeedback
from user.models import SearchHistory
from recommender.models import SummaryViewLog, SummaryRanking, SummaryClickLog
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Sum as DbSum
import logging
from functools import reduce
import operator
from django.utils import timezone
import datetime
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.core.cache import cache
import math
import uuid
from ..recommenders.recommender_controller import recommender_controller as recommender_logic

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5
MIN_RANK_THRESHOLD = 0.05
RECOMMENDATION_CANDIDATE_WINDOW_DAYS = 30 # Limit candidates to recent summaries
VIEW_DURATION_THRESHOLD = Decimal('3.0')
CATEGORY_WEIGHT = 0.5
SEARCH_HISTORY_WEIGHT = 0.3
FAVORITE_KEYWORDS_WEIGHT = 0.2
MIN_TOTAL_SCORE_TO_SAVE = 0.1

def _clear_user_softmax_cache(user_id):
    cache_key_prefix = f"user_{user_id}_softmax_cat"
    cache.delete(f"{cache_key_prefix}_sum_exp_d")
    cache.delete(f"{cache_key_prefix}_sum_exp_c")
    cache.delete(f"{cache_key_prefix}_max_d")
    cache.delete(f"{cache_key_prefix}_max_c")

def _update_summary_ranking(summary_id, user_id, category_id=None):
    if not user_id:
        return None

    try:
        ranking, created = SummaryRanking.objects.get_or_create(
            summary_id=summary_id,
            user_id=user_id,
            defaults={
                'category_score': 0.0,
                'search_history_score': 0.0,
                'favorite_keywords_score': 0.0,
                'total_score': 0.0
            }
        )

        made_significant_change = False
        if category_id:
            summaries_in_category_ids = NewsSummary.objects.filter(
                article_id__in=NewsArticleCategory.objects.filter(
                    category_id=category_id
                ).values_list('article_id', flat=True)
            ).values_list('id', flat=True)

            sum_of_qualified_view_durations = SummaryViewLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids,
                duration_seconds__gte=VIEW_DURATION_THRESHOLD
            ).aggregate(
                total_duration=DbSum('duration_seconds')
            )['total_duration'] or Decimal('0.0')

            user_category_clicks = SummaryClickLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids
            ).count()
            
            new_calculated_category_score = _calculate_category_score_softmax_service(
                current_category_duration=sum_of_qualified_view_durations,
                current_category_clicks=user_category_clicks,
                user_id=str(user_id),
                current_category_id=str(category_id)
            )
            ranking.category_score = new_calculated_category_score
            made_significant_change = True

        new_total_score = recommender_logic.calculate_total_score_from_components(
            ranking.category_score,
            ranking.search_history_score,
            ranking.favorite_keywords_score,
            CATEGORY_WEIGHT,
            SEARCH_HISTORY_WEIGHT,
            FAVORITE_KEYWORDS_WEIGHT
        )

        if ranking.total_score != new_total_score:
            ranking.total_score = new_total_score
            made_significant_change = True
        
        if ranking.total_score < MIN_TOTAL_SCORE_TO_SAVE:
            if created:
                ranking.delete()
            return None
        elif made_significant_change or created:
            ranking.save()
            
        return ranking
    except Exception as e:
        logger.error(f"Error updating summary ranking for summary {summary_id}, user {user_id}: {e}", exc_info=True)
        return None


def update_user_based_category_rankings(
        user_id, interacted_summary_id):
    if not user_id:
        return

    try:
        interacted_summary = get_object_or_404(
            NewsSummary, id=interacted_summary_id)
        article_id = interacted_summary.article_id
        if not article_id:
            return

        article_category_relation = NewsArticleCategory.objects.filter(
            article_id=article_id).first()
        if not article_category_relation:
            return

        category_id = article_category_relation.category_id
        if not category_id:
            return

        related_category_summaries = NewsSummary.objects.filter(
            article_id__in=NewsArticleCategory.objects.filter(
                category_id=category_id
            ).values_list('article_id', flat=True)
        ).exclude(id=interacted_summary_id)

        for related_summary in related_category_summaries:
            _update_summary_ranking(
                related_summary.id,
                user_id=user_id,
                category_id=category_id
            )

    except NewsSummary.DoesNotExist:
        logger.warning(
            f"Interacted summary with id {interacted_summary_id} not found for triggering related item ranking update.")
    except Exception as e:
        logger.error(
            f"Error triggering category ranking update for related items of summary {interacted_summary_id} for user {user_id}: {e}",
            exc_info=True)


def log_summary_view(user_id, summary_id, duration_seconds):
    actual_user_id = user_id

    if not actual_user_id:
        logger.info("Attempted to log summary view without user_id. Skipping.")
        return Decimal('0.0')

    try:
        summary = get_object_or_404(NewsSummary, id=summary_id)

        SummaryViewLog.objects.create(
            user_id=actual_user_id,
            summary_id=summary.id,
            duration_seconds=duration_seconds
        )
        _clear_user_softmax_cache(str(actual_user_id))

        total_duration_for_summary = SummaryViewLog.objects.filter(
            user_id=actual_user_id,
            summary_id=summary.id
        ).aggregate(
            total_duration=DbSum('duration_seconds')
        )['total_duration'] or Decimal('0.0')

        if duration_seconds >= VIEW_DURATION_THRESHOLD and actual_user_id:
            article_category_relation = NewsArticleCategory.objects.filter(
                article_id=summary.article_id
            ).first()
            if article_category_relation and article_category_relation.category_id:
                _update_summary_ranking(
                    summary_id=summary.id,
                    user_id=actual_user_id,
                    category_id=article_category_relation.category_id
                )
            update_user_based_category_rankings(
                actual_user_id, summary.id)

        return total_duration_for_summary

    except NewsSummary.DoesNotExist:
        raise
    except Exception as e:
        raise


def handle_summary_click_for_ranking(user_id, summary_id):
    try:
        summary = get_object_or_404(NewsSummary, id=summary_id)
        if user_id:
            article_category_relation = NewsArticleCategory.objects.filter(
                article_id=summary.article_id
            ).first()
            if article_category_relation and article_category_relation.category_id:
                _update_summary_ranking(
                    summary_id=summary.id,
                    user_id=user_id,
                    category_id=article_category_relation.category_id
                )
            update_user_based_category_rankings(
                user_id, summary.id)
            return {"message": "Click processed for ranking update."}
        else:
            return {"message": "Click logged, no ranking update for anonymous user."}
    except NewsSummary.DoesNotExist:
        raise
    except Exception as e:
        raise


def process_summary_click_service(user_id, summary_id_from_request):
    if not user_id:
        logger.info("Attempted to process summary click without user_id. Skipping log and ranking.")
        try:
            summary_object_for_stats = get_object_or_404(NewsSummary, id=summary_id_from_request)
            if summary_object_for_stats.article_id:
                 ArticleStats.objects.update_or_create(
                    article_id=summary_object_for_stats.article_id,
                    defaults={'view_count': F('view_count') + 1}
                )
            return {"message": "Click processed for general stats only (anonymous user)."} 
        except NewsSummary.DoesNotExist:
            raise
        except Exception as e_stats:
            logger.error(f"Error updating general stats for anonymous click on summary {summary_id_from_request}: {e_stats}")
            raise

    try:
        summary_object = get_object_or_404(NewsSummary, id=summary_id_from_request)

        SummaryClickLog.objects.create(
            user_id=user_id, 
            summary_id=summary_object.id
        )
        _clear_user_softmax_cache(str(user_id))
        
        if summary_object.article_id:
            try:
                article_stats = ArticleStats.objects.get(article_id=summary_object.article_id)
                article_stats.view_count = F('view_count') + 1
                article_stats.save(update_fields=['view_count'])
            except ArticleStats.DoesNotExist:
                ArticleStats.objects.create(article_id=summary_object.article_id, view_count=1)

        ranking_response = handle_summary_click_for_ranking(user_id, summary_object.id)

        return {
            "message": "Click tracked, stats updated, and ranking processed successfully.",
            "details": ranking_response.get("message", "Ranking update processed.")
        }

    except NewsSummary.DoesNotExist:
        raise 
    except Exception as e:
        logger.error(f"Error processing summary click for summary {summary_id_from_request}, user {user_id}: {e}", exc_info=True)
        raise


def _batch_get_fts_scores(summary_ids: list[uuid.UUID], keywords: list[str]) -> dict[uuid.UUID, float]:
    if not keywords or not summary_ids:
        return {}
    
    valid_keywords = [kw for kw in keywords if kw and isinstance(kw, str)]
    if not valid_keywords:
        return {}

    fts_queries = [SearchQuery(kw, search_type='plain', config='vietnamese') for kw in valid_keywords]
    combined_fts_query = reduce(operator.or_, fts_queries)

    summaries_with_rank = NewsSummary.objects.filter(id__in=summary_ids).annotate(
        fts_rank=SearchRank(F('search_vector'), combined_fts_query)
    ).values('id', 'fts_rank')
    
    return {item['id']: float(item['fts_rank'] or 0.0) for item in summaries_with_rank}

def _batch_calculate_initial_category_scores(user_id: str, article_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
    if not user_id or not article_ids:
        return {}

    all_interactions = _get_all_user_category_interactions_service(user_id)
    if not all_interactions:
        return {aid: 0.0 for aid in article_ids}

    article_to_category_map = dict(NewsArticleCategory.objects.filter(
        article_id__in=list(set(article_ids))
    ).values_list('article_id', 'category_id'))

    all_durations = [item['duration'] for item in all_interactions]
    all_clicks = [item['clicks'] for item in all_interactions]
    max_d_overall = max(all_durations) if all_durations else Decimal('0.0')
    max_c_overall = max(all_clicks) if all_clicks else Decimal('0.0')
    
    try:
        exp_d_values = [math.exp(float(d - max_d_overall)) for d in all_durations]
        exp_c_values = [math.exp(float(c - max_c_overall)) for c in all_clicks]
    except OverflowError:
        return {aid: 0.0 for aid in article_ids}

    sum_exp_d_all = Decimal(str(sum(exp_d_values)))
    sum_exp_c_all = Decimal(str(sum(exp_c_values)))
    
    category_interaction_map = {str(item['category_id']): item for item in all_interactions}
    scores = {}

    for article_id in article_ids:
        category_id = article_to_category_map.get(article_id)
        if not category_id:
            scores[article_id] = 0.0
            continue
        
        interaction = category_interaction_map.get(str(category_id), {'duration': Decimal('0'), 'clicks': Decimal('0')})
        
        try:
            exp_d_current = Decimal(str(math.exp(float(interaction['duration'] - max_d_overall))))
            exp_c_current = Decimal(str(math.exp(float(interaction['clicks'] - max_c_overall))))
        except OverflowError:
            scores[article_id] = 0.0
            continue

        score = recommender_logic.finalize_softmax_category_score(
            sum_exp_d_all=sum_exp_d_all, sum_exp_c_all=sum_exp_c_all,
            exp_d_current=exp_d_current, exp_c_current=exp_c_current
        )
        scores[article_id] = score
    
    return scores

def _batch_calculate_new_rankings(user_id, summaries_to_rank, sh_keywords, fk_keywords):
    if not summaries_to_rank:
        return [], []

    summary_ids_to_rank = [s.id for s in summaries_to_rank]
    article_ids_to_rank = [s.article_id for s in summaries_to_rank if s.article_id]

    sh_scores = _batch_get_fts_scores(summary_ids_to_rank, sh_keywords)
    fk_scores = _batch_get_fts_scores(summary_ids_to_rank, fk_keywords)
    category_scores = _batch_calculate_initial_category_scores(user_id, article_ids_to_rank)

    newly_ranked_summaries = []
    new_rankings_to_create = []

    for summary in summaries_to_rank:
        cat_score = category_scores.get(summary.article_id, 0.0) if summary.article_id else 0.0
        sh_score = sh_scores.get(summary.id, 0.0)
        fk_score = fk_scores.get(summary.id, 0.0)

        total_score = recommender_logic.calculate_total_score_from_components(
            cat_score, sh_score, fk_score,
            CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
        )
        summary.score = total_score
        newly_ranked_summaries.append(summary)

        if total_score >= MIN_TOTAL_SCORE_TO_SAVE:
            new_rankings_to_create.append(SummaryRanking(
                summary_id=summary.id, user_id=user_id,
                category_score=cat_score, search_history_score=sh_score,
                favorite_keywords_score=fk_score, total_score=total_score
            ))
            
    return newly_ranked_summaries, new_rankings_to_create


def get_recommendations_for_user(
        user_id,
        current_summary_id=None,
        limit=10,
        offset=0):
    if not user_id:
        return [], {}, {'type': 'auth_required', 'message': 'Cần đăng nhập để nhận đề xuất cá nhân hóa'}

    try:
        downvoted_summary_ids = list(SummaryFeedback.objects.filter(
            user_id=user_id, is_upvote=False
        ).values_list('summary_id', flat=True))

        search_history_keywords = list(SearchHistory.objects.filter(
            user_id=user_id,
            created_at__gte=timezone.now() - datetime.timedelta(days=7)
        ).values_list('query', flat=True).distinct())

        favorite_keywords_data = []
        try:
            user_pref = UserPreference.objects.get(user_id=user_id)
            if user_pref.favorite_keywords and isinstance(user_pref.favorite_keywords, list):
                favorite_keywords_data = [kw for kw in user_pref.favorite_keywords if kw and isinstance(kw, str)]
        except UserPreference.DoesNotExist:
            pass

        candidate_summaries_qs = NewsSummary.objects.filter(
            created_at__gte=timezone.now() - datetime.timedelta(days=RECOMMENDATION_CANDIDATE_WINDOW_DAYS)
        ).exclude(id__in=downvoted_summary_ids)

        if current_summary_id:
            candidate_summaries_qs = candidate_summaries_qs.exclude(id=current_summary_id)
        
        all_candidate_summaries = list(candidate_summaries_qs)
        all_candidate_summary_ids = [s.id for s in all_candidate_summaries]

        existing_rankings = SummaryRanking.objects.filter(user_id=user_id, summary_id__in=all_candidate_summary_ids)
        existing_rankings_map = {r.summary_id: r for r in existing_rankings}
        
        summaries_with_score = []
        summaries_needing_ranking = []

        for summary in all_candidate_summaries:
            if summary.id in existing_rankings_map:
                summary.score = existing_rankings_map[summary.id].total_score
                summaries_with_score.append(summary)
            else:
                summaries_needing_ranking.append(summary)

        if summaries_needing_ranking:
            newly_ranked_summaries, new_rankings_to_create = _batch_calculate_new_rankings(
                user_id, summaries_needing_ranking, search_history_keywords, favorite_keywords_data
            )
            summaries_with_score.extend(newly_ranked_summaries)
            if new_rankings_to_create:
                SummaryRanking.objects.bulk_create(new_rankings_to_create, ignore_conflicts=True)

        sorted_summaries = sorted(
            summaries_with_score,
            key=lambda x: (x.score, getattr(x, 'created_at', timezone.now())),
            reverse=True
        )

        total_recommended_count = len(sorted_summaries)
        paginated_summaries = sorted_summaries[offset:offset + limit]

        if not paginated_summaries:
            return [], {}, {'type': 'empty', 'message': 'Không có đề xuất nào khả dụng'}

        article_ids_to_fetch = [s.article_id for s in paginated_summaries if s.article_id]
        articles_qs = NewsArticle.objects.filter(id__in=list(set(article_ids_to_fetch)))
        articles_dict = {str(article.id): article for article in articles_qs}

        return paginated_summaries, articles_dict, {
            'type': 'success', 'message': 'Đã lấy đề xuất thành công',
            'total_count': total_recommended_count, 'has_more': total_recommended_count > (offset + limit)
        }
    except Exception as e:
        logger.error(f"Error in get_recommendations_for_user: {e}", exc_info=True)
        return [], {}, {'type': 'error', 'message': str(e)}


def _batch_update_fts_scores(user_id, keywords_list, score_field_name, score_weight):
    if not user_id:
        return

    # Get all existing rankings for the user to be updated.
    user_rankings_qs = SummaryRanking.objects.filter(user_id=user_id)
    summary_ids = user_rankings_qs.values_list('summary_id', flat=True)

    if not summary_ids.exists():
        logger.info(f"No existing rankings to update for user {user_id} for score '{score_field_name}'.")
        return

    # Handle empty keywords: reset scores to 0.
    valid_keywords = [kw for kw in keywords_list if kw and isinstance(kw, str)]
    if not valid_keywords:
        rankings_to_update = []
        for ranking in user_rankings_qs:
            if getattr(ranking, score_field_name) != 0.0:
                setattr(ranking, score_field_name, 0.0)
                ranking.total_score = recommender_logic.calculate_total_score_from_components(
                    ranking.category_score, ranking.search_history_score, ranking.favorite_keywords_score,
                    CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
                )
                rankings_to_update.append(ranking)
        if rankings_to_update:
            SummaryRanking.objects.bulk_update(rankings_to_update, [score_field_name, 'total_score', 'updated_at'])
            logger.info(f"Reset {score_field_name} to 0 for {len(rankings_to_update)} rankings for user {user_id}.")
        return

    # Build FTS query
    fts_queries = [SearchQuery(kw, search_type='plain', config='vietnamese') for kw in valid_keywords]
    combined_fts_query = reduce(operator.or_, fts_queries)

    # Get all FTS scores in one query
    summaries_with_rank = NewsSummary.objects.filter(id__in=summary_ids).annotate(
        fts_rank=SearchRank(F('search_vector'), combined_fts_query)
    ).values('id', 'fts_rank')
    
    summary_rank_map = {str(item['id']): float(item['fts_rank'] or 0.0) for item in summaries_with_rank}
    
    # Prepare for bulk update
    rankings_to_update = []
    # Fetch all at once to avoid N+1 issues
    user_rankings_list = list(user_rankings_qs)
    
    for ranking in user_rankings_list:
        new_score = summary_rank_map.get(str(ranking.summary_id), 0.0)
        current_score = getattr(ranking, score_field_name)

        if abs(current_score - new_score) > 1e-9: # Compare floats
            setattr(ranking, score_field_name, new_score)
            ranking.total_score = recommender_logic.calculate_total_score_from_components(
                ranking.category_score, ranking.search_history_score, ranking.favorite_keywords_score,
                CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
            )
            ranking.updated_at = timezone.now()
            rankings_to_update.append(ranking)

    if rankings_to_update:
        SummaryRanking.objects.bulk_update(rankings_to_update, [score_field_name, 'total_score', 'updated_at'])
        logger.info(f"Bulk updated {len(rankings_to_update)} rankings for user {user_id} for score '{score_field_name}'.")

def update_user_search_history_rankings(user_id):
    if not user_id:
        logger.warning("User ID not provided for search history ranking update.")
        return
    try:
        search_history_keywords = list(SearchHistory.objects.filter(
            user_id=user_id,
            created_at__gte=timezone.now() - datetime.timedelta(days=7)
        ).values_list('query', flat=True).distinct())
        
        _batch_update_fts_scores(user_id, search_history_keywords, 'search_history_score', SEARCH_HISTORY_WEIGHT)
        
        logger.info(f"Finished updating search history based rankings for user {user_id}.")
    except Exception as e:
        logger.error(f"Error updating search history rankings for user {user_id}: {e}", exc_info=True)


def update_user_favorite_keywords_rankings(user_id):
    if not user_id:
        logger.warning("User ID not provided for favorite keywords ranking update.")
        return
    try:
        favorite_keywords_data = []
        try:
            user_pref = UserPreference.objects.get(user_id=user_id)
            if user_pref.favorite_keywords and isinstance(user_pref.favorite_keywords, list):
                favorite_keywords_data = [kw for kw in user_pref.favorite_keywords if kw and isinstance(kw, str)]
        except UserPreference.DoesNotExist:
            logger.info(f"User {user_id} has no UserPreference. Skipping favorite keywords ranking update.")
        
        _batch_update_fts_scores(user_id, favorite_keywords_data, 'favorite_keywords_score', FAVORITE_KEYWORDS_WEIGHT)

        logger.info(f"Finished updating favorite keywords based rankings for user {user_id}.")
    except Exception as e:
        logger.error(f"Error updating favorite keywords rankings for user {user_id}: {e}", exc_info=True)


def _get_all_user_category_interactions_service(user_id: str):

    view_logs_data = list(SummaryViewLog.objects.filter(
        user_id=user_id,
        duration_seconds__gte=VIEW_DURATION_THRESHOLD
    ).values('summary_id', 'duration_seconds'))

    click_logs_data = list(SummaryClickLog.objects.filter(
        user_id=user_id
    ).values('summary_id'))
    
    interacted_summary_ids = {log['summary_id'] for log in view_logs_data} | \
                             {log['summary_id'] for log in click_logs_data}

    if not interacted_summary_ids:
        return []

    summary_article_map = {
        item['id']: item['article_id'] 
        for item in NewsSummary.objects.filter(
            id__in=interacted_summary_ids,
            article_id__isnull=False
        ).values('id', 'article_id')
    }

    if not summary_article_map:
        return []

    article_ids_with_summaries = list(summary_article_map.values())
    article_category_map = {
        item['article_id']: item['category_id']
        for item in NewsArticleCategory.objects.filter(
            article_id__in=article_ids_with_summaries
        ).values('article_id', 'category_id')
    }
    
    summary_category_map = {
        summary_id: article_category_map.get(article_id)
        for summary_id, article_id in summary_article_map.items()
        if article_category_map.get(article_id) is not None
    }

    category_interactions = {}

    for log in view_logs_data:
        category_id = summary_category_map.get(log['summary_id'])
        if category_id:
            cat_id_str = str(category_id)
            category_interactions.setdefault(cat_id_str, {'duration': Decimal('0.0'), 'clicks': Decimal('0.0')})
            category_interactions[cat_id_str]['duration'] += log['duration_seconds']
    
    click_counts_by_category = {}
    for log in click_logs_data:
        category_id = summary_category_map.get(log['summary_id'])
        if category_id:
            cat_id_str = str(category_id)
            click_counts_by_category.setdefault(cat_id_str, 0)
            click_counts_by_category[cat_id_str] += 1
            
    for cat_id_str, count in click_counts_by_category.items():
        category_interactions.setdefault(cat_id_str, {'duration': Decimal('0.0'), 'clicks': Decimal('0.0')})
        category_interactions[cat_id_str]['clicks'] = Decimal(count)

    return [
        {'category_id': cat_id, 'duration': data['duration'], 'clicks': data['clicks']}
        for cat_id, data in category_interactions.items()
    ]


def _calculate_category_score_softmax_service(
    current_category_duration: Decimal,
    current_category_clicks: int,
    user_id: str,
    current_category_id: str
) -> float:
    cache_key_prefix = f"user_{user_id}_softmax_cat"
    cache_key_sum_exp_d = f"{cache_key_prefix}_sum_exp_d"
    cache_key_sum_exp_c = f"{cache_key_prefix}_sum_exp_c"
    cache_key_max_d = f"{cache_key_prefix}_max_d"
    cache_key_max_c = f"{cache_key_prefix}_max_c"
    CACHE_TIMEOUT_SECONDS = 300

    max_d_overall_from_cache = cache.get(cache_key_max_d)
    max_c_overall_from_cache = cache.get(cache_key_max_c)
    sum_exp_d_all_from_cache = cache.get(cache_key_sum_exp_d)
    sum_exp_c_all_from_cache = cache.get(cache_key_sum_exp_c)

    max_d_to_use: Decimal
    max_c_to_use: Decimal
    sum_exp_d_to_use: Decimal
    sum_exp_c_to_use: Decimal

    if any(v is None for v in [max_d_overall_from_cache, max_c_overall_from_cache, sum_exp_d_all_from_cache, sum_exp_c_all_from_cache]):
        all_interactions = _get_all_user_category_interactions_service(user_id)

        found_current = False
        for item in all_interactions:
            if item['category_id'] == current_category_id:
                item['duration'] = current_category_duration
                item['clicks'] = Decimal(current_category_clicks)
                found_current = True
                break
        if not found_current and current_category_id:
             all_interactions.append({
                'category_id': current_category_id,
                'duration': current_category_duration,
                'clicks': Decimal(current_category_clicks)
            })
        
        if not all_interactions:
            return 0.0

        all_durations = [item['duration'] for item in all_interactions]
        all_clicks = [item['clicks'] for item in all_interactions]

        max_d_to_use = max(all_durations) if all_durations else Decimal('0.0')
        max_c_to_use = max(all_clicks) if all_clicks else Decimal('0.0')
        
        try:
            exp_d_values = [math.exp(float(d - max_d_to_use)) for d in all_durations]
            exp_c_values = [math.exp(float(c - max_c_to_use)) for c in all_clicks]
        except OverflowError:
            logger.error(f"OverflowError during service-side softmax component calculation for user {user_id}. Durations: {all_durations}, Clicks: {all_clicks}")
            return 0.0

        sum_exp_d_to_use = Decimal(str(sum(exp_d_values)))
        sum_exp_c_to_use = Decimal(str(sum(exp_c_values)))

        cache.set(cache_key_max_d, max_d_to_use, CACHE_TIMEOUT_SECONDS)
        cache.set(cache_key_max_c, max_c_to_use, CACHE_TIMEOUT_SECONDS)
        cache.set(cache_key_sum_exp_d, sum_exp_d_to_use, CACHE_TIMEOUT_SECONDS)
        cache.set(cache_key_sum_exp_c, sum_exp_c_to_use, CACHE_TIMEOUT_SECONDS)
    else:
        max_d_to_use = max_d_overall_from_cache
        max_c_to_use = max_c_overall_from_cache
        sum_exp_d_to_use = sum_exp_d_all_from_cache
        sum_exp_c_to_use = sum_exp_c_all_from_cache

    try:
        exp_d_current = Decimal(str(math.exp(float(current_category_duration - max_d_to_use))))
        exp_c_current = Decimal(str(math.exp(float(Decimal(current_category_clicks) - max_c_to_use))))
    except OverflowError:
        logger.error(f"OverflowError during current category exponentiation for user {user_id}, category {current_category_id}.")
        return 0.0

    final_category_score = recommender_logic.finalize_softmax_category_score(
        sum_exp_d_all=sum_exp_d_to_use,
        sum_exp_c_all=sum_exp_c_to_use,
        exp_d_current=exp_d_current,
        exp_c_current=exp_c_current
    )
    return final_category_score
