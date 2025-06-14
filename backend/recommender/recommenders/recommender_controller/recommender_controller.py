import math
from decimal import Decimal
from recommender.services import recommend_service


def calculate_softmax_components_for_category(
    all_category_interactions_data: list[dict],
    current_category_id: str,
    current_category_duration: Decimal,  # d_c
    current_category_clicks: int  # c_c
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    if not all_category_interactions_data:
        return Decimal('0.0'), Decimal('0.0'), Decimal(
            '0.0'), Decimal('0.0'), Decimal('0.0'), Decimal('0.0')

    all_durations = [item['duration']
                     for item in all_category_interactions_data]
    all_clicks = [item['clicks'] for item in all_category_interactions_data]

    max_d_overall = max(all_durations) if all_durations else Decimal('0.0')
    max_c_overall = max(all_clicks) if all_clicks else Decimal('0.0')

    exp_d_values = []
    exp_c_values = []

    try:
        for item_duration in all_durations:
            exp_d_values.append(math.exp(float(item_duration - max_d_overall)))
        for item_clicks in all_clicks:
            exp_c_values.append(math.exp(float(item_clicks - max_c_overall)))
    except OverflowError:
        return Decimal('0.0'), Decimal('0.0'), Decimal(
            '0.0'), Decimal('0.0'), Decimal('0.0'), Decimal('0.0')

    sum_exp_d_all = Decimal(str(sum(exp_d_values)))
    sum_exp_c_all = Decimal(str(sum(exp_c_values)))

    try:
        exp_d_current = Decimal(
            str(math.exp(float(current_category_duration - max_d_overall))))
        exp_c_current = Decimal(
            str(math.exp(float(Decimal(current_category_clicks) - max_c_overall))))
    except OverflowError:
        return Decimal('0.0'), Decimal(
            '0.0'), sum_exp_d_all, sum_exp_c_all, Decimal('0.0'), Decimal('0.0')

    return max_d_overall, max_c_overall, sum_exp_d_all, sum_exp_c_all, exp_d_current, exp_c_current


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
