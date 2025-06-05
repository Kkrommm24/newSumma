from news.models import NewsArticle, NewsArticleCategory, ArticleStats
from user.models import UserPreference
from summarizer.models import NewsSummary
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
from ..recommenders.recommender_controller import recommender_controller as recommender_logic

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5
MIN_RANK_THRESHOLD = 0.05
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

def _calculate_fts_score_for_summary(summary_obj, keywords_list: list[str], search_config='vietnamese') -> float:
    if not keywords_list or not summary_obj or not summary_obj.search_vector:
        return 0.0

    valid_keywords = [kw for kw in keywords_list if kw and isinstance(kw, str)]
    if not valid_keywords:
        return 0.0

    fts_queries = [
        SearchQuery(kw, search_type='plain', config=search_config)
        for kw in valid_keywords
    ]

    if not fts_queries:
        return 0.0

    combined_fts_query = reduce(operator.or_, fts_queries)

    summary_rank_data = NewsSummary.objects.filter(pk=summary_obj.pk).annotate(
        rank=SearchRank(F('search_vector'), combined_fts_query)
    ).values('rank').first()

    if summary_rank_data and summary_rank_data['rank'] is not None:
        return float(summary_rank_data['rank'])
    return 0.0


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


def get_recommendations_for_user(
        user_id,
        current_summary_id=None,
        limit=10,
        offset=0):
    if not user_id:
        return [], {}, {
            'type': 'auth_required',
            'message': 'Cần đăng nhập để nhận đề xuất cá nhân hóa'
        }

    try:
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

        summaries_qs = NewsSummary.objects.all()
        if current_summary_id:
            summaries_qs = summaries_qs.exclude(id=current_summary_id)

        user_rankings = SummaryRanking.objects.filter(
            user_id=user_id,
            summary_id__in=summaries_qs.values_list('id', flat=True)
        )
        rankings_dict = {str(r.summary_id): r for r in user_rankings}

        summaries_with_score = []
        for summary in summaries_qs:
            ranking = rankings_dict.get(str(summary.id))
            if ranking:
                summary.score = ranking.total_score
            else:
                try:
                    category_score = _calculate_initial_category_score(user_id, summary.article_id)
                    sh_score = _calculate_fts_score_for_summary(summary, search_history_keywords)
                    fk_score = _calculate_fts_score_for_summary(summary, favorite_keywords_data)

                    calculated_total_score = recommender_logic.calculate_total_score_from_components(
                        category_score, sh_score, fk_score,
                        CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
                    )
                    
                    if calculated_total_score >= MIN_TOTAL_SCORE_TO_SAVE:
                        new_ranking = SummaryRanking.objects.create(
                            summary_id=summary.id, user_id=user_id,
                            category_score=category_score, search_history_score=sh_score,
                            favorite_keywords_score=fk_score, total_score=calculated_total_score
                        )
                        summary.score = new_ranking.total_score
                    else:
                        summary.score = calculated_total_score

                except Exception as e_create_ranking:
                    logger.error(f"Error creating new ranking for summary {summary.id}: {e_create_ranking}", exc_info=True)
                    summary.score = 0
            summaries_with_score.append(summary)

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


def update_user_search_history_rankings(user_id):
    if not user_id:
        logger.warning("User ID not provided for search history ranking update.")
        return
    try:
        search_history_keywords = list(SearchHistory.objects.filter(
            user_id=user_id,
            created_at__gte=timezone.now() - datetime.timedelta(days=7)
        ).values_list('query', flat=True).distinct())

        user_rankings = SummaryRanking.objects.filter(user_id=user_id)
        
        summaries_to_update_ids = user_rankings.values_list('summary_id', flat=True)
        summaries_dict = {str(s.id): s for s in NewsSummary.objects.filter(id__in=summaries_to_update_ids)}

        for ranking in user_rankings:
            summary = summaries_dict.get(str(ranking.summary_id))
            if not summary:
                continue

            new_sh_score = _calculate_fts_score_for_summary(summary, search_history_keywords)
            if ranking.search_history_score != new_sh_score:
                ranking.search_history_score = new_sh_score
                ranking.total_score = recommender_logic.calculate_total_score_from_components(
                    ranking.category_score, ranking.search_history_score, ranking.favorite_keywords_score,
                    CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
                )
                ranking.save(update_fields=['search_history_score', 'total_score', 'updated_at'])
        logger.info(f"Finished updating search history based rankings for existing entries of user {user_id}.")
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

            logger.info(f"User {user_id} has no UserPreference or favorite keywords. Skipping favorite keywords ranking update.")
            return
        
        if not favorite_keywords_data:
            user_rankings_to_reset = SummaryRanking.objects.filter(user_id=user_id)
            updated_count = 0
            for ranking in user_rankings_to_reset:
                if ranking.favorite_keywords_score != 0.0:
                    ranking.favorite_keywords_score = 0.0
                    ranking.total_score = recommender_logic.calculate_total_score_from_components(
                        ranking.category_score, ranking.search_history_score, ranking.favorite_keywords_score,
                        CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
                    )
                    ranking.save(update_fields=['favorite_keywords_score', 'total_score', 'updated_at'])
                    updated_count +=1
            if updated_count > 0:
                 logger.info(f"Reset favorite_keywords_score to 0 for {updated_count} existing rankings for user {user_id} due to empty favorite list.")
            return

        # Chỉ lấy và cập nhật các bản ghi SummaryRanking đã tồn tại cho user_id này
        user_rankings = SummaryRanking.objects.filter(user_id=user_id)
        
        summaries_to_update_ids = user_rankings.values_list('summary_id', flat=True)
        summaries_dict = {str(s.id): s for s in NewsSummary.objects.filter(id__in=summaries_to_update_ids)}

        for ranking in user_rankings:
            summary = summaries_dict.get(str(ranking.summary_id))
            if not summary: # Bỏ qua nếu tóm tắt không còn tồn tại
                continue
                
            new_fk_score = _calculate_fts_score_for_summary(summary, favorite_keywords_data)
            if ranking.favorite_keywords_score != new_fk_score:
                ranking.favorite_keywords_score = new_fk_score
                ranking.total_score = recommender_logic.calculate_total_score_from_components(
                    ranking.category_score, ranking.search_history_score, ranking.favorite_keywords_score,
                    CATEGORY_WEIGHT, SEARCH_HISTORY_WEIGHT, FAVORITE_KEYWORDS_WEIGHT
                )
                ranking.save(update_fields=['favorite_keywords_score', 'total_score', 'updated_at'])
        logger.info(f"Finished updating favorite keywords based rankings for existing entries of user {user_id}.")
    except Exception as e:
        logger.error(f"Error updating favorite keywords rankings for user {user_id}: {e}", exc_info=True)


def _calculate_initial_category_score(user_id, summary_article_id):
    if not user_id or not summary_article_id:
        return 0.0
    try:
        article = NewsArticle.objects.filter(id=summary_article_id).first()
        if not article:
            return 0.0
        
        article_category_relation = NewsArticleCategory.objects.filter(article_id=article.id).first()
        if not article_category_relation or not article_category_relation.category_id:
            return 0.0
        
        category_id = article_category_relation.category_id

        summaries_in_category_ids = NewsSummary.objects.filter(
            article_id__in=NewsArticleCategory.objects.filter(
                category_id=category_id
            ).values_list('article_id', flat=True)
        ).values_list('id', flat=True)

        current_category_duration = SummaryViewLog.objects.filter(
            user_id=user_id,
            summary_id__in=summaries_in_category_ids,
            duration_seconds__gte=VIEW_DURATION_THRESHOLD
        ).aggregate(total_duration=DbSum('duration_seconds'))['total_duration'] or Decimal('0.0')

        current_category_clicks = SummaryClickLog.objects.filter(
            user_id=user_id,
            summary_id__in=summaries_in_category_ids
        ).count()

        initial_category_score = _calculate_category_score_softmax_service(
            current_category_duration=current_category_duration,
            current_category_clicks=current_category_clicks,
            user_id=str(user_id),
            current_category_id=str(category_id)
        )
        return float(initial_category_score)

    except Exception as e:
        logger.error(f"Error calculating initial category score for article {summary_article_id}, user {user_id}: {e}", exc_info=True)
        return 0.0

def _get_all_user_category_interactions_service(user_id: str):
    viewed_summaries_qs = SummaryViewLog.objects.filter(
        user_id=user_id,
        duration_seconds__gte=VIEW_DURATION_THRESHOLD
    ).values_list('summary_id', flat=True).distinct()

    clicked_summaries_qs = SummaryClickLog.objects.filter(
        user_id=user_id
    ).values_list('summary_id', flat=True).distinct()
    
    all_interacted_summary_ids = set(list(viewed_summaries_qs)) | set(list(clicked_summaries_qs))
    if not all_interacted_summary_ids:
        return []

    article_ids_for_summaries = NewsSummary.objects.filter(id__in=all_interacted_summary_ids)\
        .exclude(article_id__isnull=True)\
        .values_list('article_id', flat=True).distinct()

    if not article_ids_for_summaries:
        return []

    article_to_category_relations = NewsArticleCategory.objects.filter(article_id__in=article_ids_for_summaries)\
        .values('category_id').distinct()
    
    unique_category_ids = {rel['category_id'] for rel in article_to_category_relations}

    category_interactions_data = []
    for cat_id_obj in unique_category_ids:
        cat_id = str(cat_id_obj)
        summaries_in_this_category = NewsSummary.objects.filter(
            article_id__in=NewsArticleCategory.objects.filter(category_id=cat_id).values_list('article_id', flat=True)
        ).values_list('id', flat=True)
        
        relevant_summaries_in_cat_ids = all_interacted_summary_ids.intersection(set(summaries_in_this_category))

        if not relevant_summaries_in_cat_ids:
            cat_total_duration = Decimal('0.0')
            cat_total_clicks = 0
        else:
            cat_total_duration = SummaryViewLog.objects.filter(
                user_id=user_id,
                summary_id__in=relevant_summaries_in_cat_ids,
                duration_seconds__gte=VIEW_DURATION_THRESHOLD
            ).aggregate(total_duration=DbSum('duration_seconds'))['total_duration'] or Decimal('0.0')

            cat_total_clicks = SummaryClickLog.objects.filter(
                user_id=user_id,
                summary_id__in=relevant_summaries_in_cat_ids
            ).count()
        
        category_interactions_data.append({
            'category_id': cat_id,
            'duration': cat_total_duration,
            'clicks': Decimal(cat_total_clicks)
        })
    return category_interactions_data


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
