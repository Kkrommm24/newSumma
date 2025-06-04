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
import math
from recommender.recommenders.recommender_controller import recommender_controller as recommender_logic

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5
MIN_RANK_THRESHOLD = 0.05
VIEW_DURATION_THRESHOLD = 3.0
CATEGORY_WEIGHT = 0.5
SEARCH_HISTORY_WEIGHT = 0.3
FAVORITE_KEYWORDS_WEIGHT = 0.2
TARGET_ENGAGEMENT_FOR_MAX_CATEGORY_SCORE = Decimal('20.0') 
DURATION_ENGAGEMENT_WEIGHT = Decimal('0.1')
CLICK_ENGAGEMENT_WEIGHT = Decimal('1.0')

LOG_CATEGORY_NORMALIZATION_DIVISOR = Decimal(str(math.log1p(float(TARGET_ENGAGEMENT_FOR_MAX_CATEGORY_SCORE))))
if LOG_CATEGORY_NORMALIZATION_DIVISOR == Decimal('0'):
    LOG_CATEGORY_NORMALIZATION_DIVISOR = Decimal('1.0')


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

        if category_id:
            summaries_in_category_ids = NewsSummary.objects.filter(
                article_id__in=NewsArticleCategory.objects.filter(
                    category_id=category_id
                ).values_list('article_id', flat=True)
            ).values_list('id', flat=True)

            qualified_view_logs = SummaryViewLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids,
                duration_seconds__gte=VIEW_DURATION_THRESHOLD
            )
            sum_of_qualified_view_durations = qualified_view_logs.aggregate(
                total_duration=DbSum('duration_seconds')
            )['total_duration'] or Decimal('0.0')

            user_category_clicks = SummaryClickLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids
            ).count()
            
            total_engagement_value = recommender_logic.calculate_category_engagement_value(
                sum_of_qualified_view_durations,
                user_category_clicks,
                DURATION_ENGAGEMENT_WEIGHT,
                CLICK_ENGAGEMENT_WEIGHT
            )
            
            normalized_score = recommender_logic.calculate_normalized_category_score(
                total_engagement_value,
                LOG_CATEGORY_NORMALIZATION_DIVISOR
            )
            ranking.category_score = normalized_score

        ranking.total_score = recommender_logic.calculate_total_score_from_components(
            ranking.category_score,
            ranking.search_history_score,
            ranking.favorite_keywords_score,
            CATEGORY_WEIGHT,
            SEARCH_HISTORY_WEIGHT,
            FAVORITE_KEYWORDS_WEIGHT
        )
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

        updated_count = 0
        for related_summary in related_category_summaries:
            _update_summary_ranking(
                related_summary.id,
                user_id=user_id,
                category_id=category_id
            )
            updated_count += 1

    except NewsSummary.DoesNotExist:
        logger.warning(
            f"Interacted summary with id {interacted_summary_id} not found for triggering related item ranking update.")
    except Exception as e:
        logger.error(
            f"Error triggering category ranking update for related items of summary {interacted_summary_id} for user {user_id}: {e}",
            exc_info=True)


def log_summary_view(user_id, summary_id, duration_seconds):
    actual_user_id = user_id

    try:
        summary = get_object_or_404(NewsSummary, id=summary_id)

        SummaryViewLog.objects.create(
            user_id=actual_user_id,
            summary_id=summary.id,
            duration_seconds=duration_seconds
        )

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
        # Ensure summary exists
        summary = get_object_or_404(NewsSummary, id=summary_id)

        if user_id:  # Only update ranking if user is authenticated
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
            return {
                "message": "Click logged, no ranking update for anonymous user."}

    except NewsSummary.DoesNotExist:
        raise
    except Exception as e:
        raise


def process_summary_click_service(user_id, summary_id_from_request):
    try:
        summary_object = get_object_or_404(NewsSummary, id=summary_id_from_request)

        SummaryClickLog.objects.create(
            user_id=user_id, # user_id từ request (đã được xác thực hoặc None)
            summary_id=summary_object.id
        )

        if summary_object.article_id:
            article_stats, created = ArticleStats.objects.get_or_create(
                article_id=summary_object.article_id,
                defaults={'view_count': 1}
            )
            if not created:
                ArticleStats.objects.filter(
                    article_id=summary_object.article_id).update(
                    view_count=F('view_count') + 1)
        
        ranking_response = handle_summary_click_for_ranking(user_id, summary_object.id)

        return {
            "message": "Click tracked, stats updated, and ranking processed successfully.",
            "details": ranking_response.get("message", "Ranking update processed.")
        }

    except NewsSummary.DoesNotExist:
        # Exception này sẽ được bắt ở view hoặc interface layer cao hơn nếu cần
        raise 
    except Exception as e:
        logger.error(f"Error processing summary click for summary {summary_id_from_request}, user {user_id}: {e}", exc_info=True)
        # Raise lại để lớp gọi có thể xử lý (ví dụ: trả về 500 error)
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

        all_summary_ids_for_ranking = summaries_qs.values_list('id', flat=True)

        user_rankings = SummaryRanking.objects.filter(
            user_id=user_id,
            summary_id__in=all_summary_ids_for_ranking
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
                        category_score,
                        sh_score,
                        fk_score,
                        CATEGORY_WEIGHT,
                        SEARCH_HISTORY_WEIGHT,
                        FAVORITE_KEYWORDS_WEIGHT
                    )

                    new_ranking = SummaryRanking.objects.create(
                        summary_id=summary.id,
                        user_id=user_id,
                        category_score=category_score,
                        search_history_score=sh_score,
                        favorite_keywords_score=fk_score,
                        total_score=calculated_total_score
                    )
                    summary.score = new_ranking.total_score
                except Exception as e_create_ranking:
                    logger.error(
                        f"Error creating or calculating ranking for summary {summary.id}: {e_create_ranking}",
                        exc_info=True)
                    summary.score = 0 # Default to 0 if error occurs

            summaries_with_score.append(summary)

        sorted_summaries = sorted(
            summaries_with_score,
            # Thêm getattr để tránh lỗi nếu created_at thiếu
            key=lambda x: (x.score, getattr(x, 'created_at', timezone.now())),
            reverse=True
        )

        total_recommended_count = len(sorted_summaries)
        paginated_summaries = sorted_summaries[offset:offset + limit]

        if not paginated_summaries:
            return [], {}, {
                'type': 'empty',
                'message': 'Không có đề xuất nào khả dụng'
            }

        article_ids_to_fetch = [
            s.article_id for s in paginated_summaries if s.article_id]

        articles_qs = NewsArticle.objects.filter(
            id__in=list(set(article_ids_to_fetch)))
        articles_dict = {str(article.id): article for article in articles_qs}

        return paginated_summaries, articles_dict, {
            'type': 'success',
            'message': 'Đã lấy đề xuất thành công',
            'total_count': total_recommended_count,
            'has_more': total_recommended_count > (offset + limit)
        }

    except Exception as e:
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

        summaries = NewsSummary.objects.all()
        for summary in summaries:
            ranking, created = SummaryRanking.objects.get_or_create(
                summary_id=summary.id,
                user_id=user_id,
                defaults={
                    'category_score': 0.0,
                    'search_history_score': 0.0,
                    'favorite_keywords_score': 0.0,
                    'total_score': 0.0
                }
            )
            
            new_sh_score = _calculate_fts_score_for_summary(summary, search_history_keywords)
            
            if ranking.search_history_score != new_sh_score:
                ranking.search_history_score = new_sh_score
                ranking.total_score = recommender_logic.calculate_total_score_from_components(
                    ranking.category_score,
                    ranking.search_history_score,
                    ranking.favorite_keywords_score,
                    CATEGORY_WEIGHT,
                    SEARCH_HISTORY_WEIGHT,
                    FAVORITE_KEYWORDS_WEIGHT
                )
                ranking.save()

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
            pass
        
        summaries = NewsSummary.objects.all()
        for summary in summaries:
            ranking, created = SummaryRanking.objects.get_or_create(
                summary_id=summary.id,
                user_id=user_id,
                defaults={
                    'category_score': 0.0,
                    'search_history_score': 0.0,
                    'favorite_keywords_score': 0.0,
                    'total_score': 0.0
                }
            )

            new_fk_score = _calculate_fts_score_for_summary(summary, favorite_keywords_data)

            if ranking.favorite_keywords_score != new_fk_score:
                ranking.favorite_keywords_score = new_fk_score
                ranking.total_score = recommender_logic.calculate_total_score_from_components(
                    ranking.category_score,
                    ranking.search_history_score,
                    ranking.favorite_keywords_score,
                    CATEGORY_WEIGHT,
                    SEARCH_HISTORY_WEIGHT,
                    FAVORITE_KEYWORDS_WEIGHT
                )
                ranking.save()
        
        logger.info(f"Finished updating favorite keywords based rankings for user {user_id}.")
    except Exception as e:
        logger.error(f"Error updating favorite keywords rankings for user {user_id}: {e}", exc_info=True)


def _calculate_initial_category_score(user_id, summary_article_id):
    if not user_id or not summary_article_id:
        return 0.0
    try:
        article_category_relation = NewsArticleCategory.objects.filter(
            article_id=summary_article_id).first()
        if article_category_relation and article_category_relation.category_id:
            category_id = article_category_relation.category_id
            
            summaries_in_category_ids = NewsSummary.objects.filter(
                article_id__in=NewsArticleCategory.objects.filter(
                    category_id=category_id
                ).values_list('article_id', flat=True)
            ).values_list('id', flat=True)

            qualified_view_logs = SummaryViewLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids,
                duration_seconds__gte=VIEW_DURATION_THRESHOLD
            )
            sum_of_qualified_view_durations = qualified_view_logs.aggregate(
                total_duration=DbSum('duration_seconds')
            )['total_duration'] or Decimal('0.0')

            user_category_clicks = SummaryClickLog.objects.filter(
                user_id=user_id,
                summary_id__in=summaries_in_category_ids
            ).count()
            
            total_engagement_value = recommender_logic.calculate_category_engagement_value(
                sum_of_qualified_view_durations,
                user_category_clicks,
                DURATION_ENGAGEMENT_WEIGHT,
                CLICK_ENGAGEMENT_WEIGHT
            )
            
            initial_category_score = recommender_logic.calculate_normalized_category_score(
                total_engagement_value,
                LOG_CATEGORY_NORMALIZATION_DIVISOR
            )
            return float(initial_category_score)

    except Exception as e:
        logger.error(f"Error calculating initial category score for article {summary_article_id}, user {user_id}: {e}", exc_info=True)
    return 0.0
