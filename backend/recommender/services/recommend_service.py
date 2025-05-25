from news.models import NewsArticle, NewsSummary, UserPreference, SearchHistory, Category, NewsArticleCategory
from recommender.models import SummaryViewLog, SummaryRanking, SummaryClickLog
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F
import logging
from functools import reduce
import operator
from django.utils import timezone
import datetime
from django.db.models import Sum
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)
SEARCH_HISTORY_LIMIT = 5
MIN_RANK_THRESHOLD = 0.05
VIEW_DURATION_THRESHOLD = 3


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
            user_category_views = SummaryViewLog.objects.filter(
                user_id=user_id,
                summary_id__in=NewsSummary.objects.filter(
                    article_id__in=NewsArticleCategory.objects.filter(
                        category_id=category_id
                    ).values_list('article_id', flat=True)
                ).values_list('id', flat=True),
                duration_seconds__gte=VIEW_DURATION_THRESHOLD
            ).count()
            ranking.category_score = min(user_category_views / 10, 1.0)

        ranking.calculate_total_score()
        return ranking
    except Exception as e:
        return None


def _trigger_category_ranking_update_for_related_items(
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
            total_duration=Sum('duration_seconds')
        )['total_duration'] or 0

        if duration_seconds >= VIEW_DURATION_THRESHOLD and actual_user_id:
            _trigger_category_ranking_update_for_related_items(
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
            _trigger_category_ranking_update_for_related_items(
                user_id, summary.id)
            return {"message": "Click processed for ranking update."}
        else:
            return {
                "message": "Click logged, no ranking update for anonymous user."}

    except NewsSummary.DoesNotExist:
        raise
    except Exception as e:
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
        # Hoàn lại cách query NewsSummary ban đầu, không dùng
        # select_related('article') dựa trên FK không tồn tại
        summaries_qs = NewsSummary.objects.all()

        if current_summary_id:
            summaries_qs = summaries_qs.exclude(id=current_summary_id)

        # Lấy tất cả ID summary để query ranking (nếu summaries_qs lớn, có thể tối ưu sau)
        # Tuy nhiên, logic xếp hạng/tạo ranking mới cần tất cả summaries tiềm
        # năng
        all_summary_ids_for_ranking = summaries_qs.values_list('id', flat=True)

        user_rankings = SummaryRanking.objects.filter(
            user_id=user_id,
            summary_id__in=all_summary_ids_for_ranking
        )
        rankings_dict = {str(r.summary_id): r for r in user_rankings}

        summaries_with_score = []
        for summary in summaries_qs:  # Lặp qua tất cả summaries tiềm năng để tính/lấy điểm
            ranking = rankings_dict.get(str(summary.id))

            if ranking:
                summary.score = ranking.total_score
            else:
                try:
                    new_ranking = SummaryRanking.objects.create(
                        summary_id=summary.id,
                        user_id=user_id,
                        category_score=0.0,
                        search_history_score=0.0,
                        favorite_keywords_score=0.0,
                        total_score=0.01  # Điểm cơ bản
                    )
                    summary.score = new_ranking.total_score
                except Exception as e_create_ranking:
                    logger.error(
                        f"Error creating ranking for summary {summary.id}: {e_create_ranking}",
                        exc_info=True)
                    summary.score = 0

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


def update_summary_rankings(user_id=None):
    try:
        summaries = NewsSummary.objects.all()

        for summary in summaries:
            try:
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

                category_score = 0.0
                article_categories = NewsArticleCategory.objects.filter(
                    article_id=summary.article_id)
                if article_categories.exists():
                    for category in article_categories:
                        category_views = SummaryViewLog.objects.filter(
                            summary_id__in=NewsSummary.objects.filter(
                                article_id__in=NewsArticleCategory.objects.filter(
                                    category_id=category.category_id
                                ).values_list('article_id', flat=True)
                            ).values_list('id', flat=True),
                            duration_seconds__gte=VIEW_DURATION_THRESHOLD
                        ).count()
                        category_score = max(
                            category_score, min(
                                category_views / 10, 1.0))

                search_history_score = 0.0
                if user_id:
                    search_history_keywords = SearchHistory.objects.filter(
                        user_id=user_id,
                        created_at__gte=timezone.now() -
                        datetime.timedelta(
                            days=7)).values_list(
                        'query',
                        flat=True)

                    if search_history_keywords:
                        search_config = 'vietnamese'
                        fts_queries = [
                            SearchQuery(
                                kw,
                                search_type='plain',
                                config=search_config) for kw in search_history_keywords if kw]
                        if fts_queries:
                            combined_fts_query = reduce(
                                operator.or_, fts_queries)

                            summary_rank_obj = NewsSummary.objects.filter(pk=summary.pk).annotate(
                                rank=SearchRank(F('search_vector'), combined_fts_query)
                            ).values('rank').first()

                            if summary_rank_obj and summary_rank_obj['rank'] is not None:
                                search_history_score = summary_rank_obj['rank']

                favorite_keywords_score = 0.0
                if user_id:
                    try:
                        user_pref = UserPreference.objects.get(user_id=user_id)
                        if user_pref.favorite_keywords:
                            fav_kws = user_pref.favorite_keywords
                            search_config = 'vietnamese'
                            fts_queries = [
                                SearchQuery(
                                    kw,
                                    search_type='plain',
                                    config=search_config) for kw in fav_kws if kw]
                            if fts_queries:
                                combined_fts_query = reduce(
                                    operator.or_, fts_queries)
                                summary_rank_obj = NewsSummary.objects.filter(pk=summary.pk).annotate(
                                    rank=SearchRank(F('search_vector'), combined_fts_query)
                                ).values('rank').first()

                                if summary_rank_obj and summary_rank_obj['rank'] is not None:
                                    favorite_keywords_score = summary_rank_obj['rank']
                    except UserPreference.DoesNotExist:
                        pass

                ranking.category_score = category_score
                ranking.search_history_score = search_history_score
                ranking.favorite_keywords_score = favorite_keywords_score
                ranking.calculate_total_score()
                ranking.save()

            except Exception as e:
                continue

    except Exception as e:
        raise
