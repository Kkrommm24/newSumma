from decimal import Decimal
from recommender.services import recommend_service

def finalize_softmax_category_score(
    sum_exp_d_all: Decimal,
    sum_exp_c_all: Decimal,
    exp_d_current: Decimal,
    exp_c_current: Decimal
) -> float:
    softmax_duration_score = (
        exp_d_current /
        sum_exp_d_all) if sum_exp_d_all > Decimal('0') else Decimal('0.0')
    softmax_click_score = (
        exp_c_current /
        sum_exp_c_all) if sum_exp_c_all > Decimal('0') else Decimal('0.0')

    final_category_score = float(
        Decimal('0.5') * (softmax_duration_score + softmax_click_score))
    return final_category_score


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


def get_recommendations_interface(
        user_id,
        current_summary_id=None,
        limit=10,
        offset=0):
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
    return recommend_service.process_summary_click_service(
        user_id=user_id,
        summary_id_from_request=summary_id
    )
