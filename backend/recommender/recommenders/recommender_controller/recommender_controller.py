import math
from decimal import Decimal
from recommender.services import recommend_service

def calculate_category_engagement_value(
    sum_of_qualified_view_durations: Decimal,
    user_category_clicks: int,
    duration_engagement_weight: Decimal,
    click_engagement_weight: Decimal
) -> Decimal:
    duration_engagement = sum_of_qualified_view_durations * duration_engagement_weight
    click_engagement = Decimal(user_category_clicks) * click_engagement_weight
    total_engagement_value = duration_engagement + click_engagement
    return total_engagement_value


def calculate_normalized_category_score(
    total_engagement_value: Decimal,
    log_category_normalization_divisor: Decimal
) -> float:
    if total_engagement_value > Decimal('0') and log_category_normalization_divisor > Decimal('0'):
        logged_engagement = Decimal(str(math.log1p(float(total_engagement_value))))
        normalized_score = logged_engagement / log_category_normalization_divisor
        return float(min(normalized_score, Decimal('1.0')))
    return 0.0


def calculate_total_score_from_components(
    category_score: float,
    search_history_score: float,
    favorite_keywords_score: float,
    category_weight: float,
    search_history_weight: float,
    favorite_keywords_weight: float
) -> float:
    total_score = (category_score * category_weight) + \
                  (search_history_score * search_history_weight) + \
                  (favorite_keywords_score * favorite_keywords_weight)
    return total_score

def get_recommendations_interface(user_id, current_summary_id=None, limit=10, offset=0):
    return recommend_service.get_recommendations_for_user(
        user_id,
        current_summary_id,
        limit=limit,
        offset=offset
    )

def log_summary_view_interface(user_id, summary_id, duration_seconds):
    return recommend_service.log_summary_view(
        user_id=user_id,
        summary_id=summary_id,
        duration_seconds=duration_seconds
    )

def track_source_click_interface(user_id, summary_id):
    """
    Interface function for views to track source click.
    Calls the new consolidated service function.
    """
    # Gọi hàm service mới đã bao gồm tất cả logic
    return recommend_service.process_summary_click_service(
        user_id=user_id,
        summary_id_from_request=summary_id
    )
