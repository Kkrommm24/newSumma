import logging
from user.models import UserPreference
from django.db import transaction
from django.utils import timezone
from recommender.services.recommend_service import update_user_favorite_keywords_rankings

logger = logging.getLogger(__name__)


def get_user_preference(user_id) -> UserPreference:
    if not user_id:
        raise ValueError("User ID cannot be empty.")
    try:
        return UserPreference.objects.get(user_id=user_id)
    except UserPreference.DoesNotExist:

        raise
    except Exception as e:
        raise


def add_favorite_keywords(
        user_id,
        keywords_to_add: list[str]) -> UserPreference:

    if not user_id or not keywords_to_add:
        raise ValueError("User ID and keywords list cannot be empty.")

    try:
        with transaction.atomic():
            preference, created = UserPreference.objects.get_or_create(
                user_id=user_id,
                defaults={'favorite_keywords': []}
            )

            current_keywords = preference.favorite_keywords or []
            if not isinstance(current_keywords, list):
                current_keywords = []

            current_keywords_lower = {kw.lower() for kw in current_keywords}
            new_keywords_added = False
            for kw in keywords_to_add:
                if kw.lower() not in current_keywords_lower:
                    current_keywords.append(kw)
                    current_keywords_lower.add(kw.lower())
                    new_keywords_added = True

            if new_keywords_added:
                preference.favorite_keywords = current_keywords
                preference.save(
                    update_fields=[
                        'favorite_keywords',
                        'updated_at'])
                try:
                    update_user_favorite_keywords_rankings(user_id=user_id)
                except Exception as e_rank:
                    logger.error(
                        f"Error triggering summary favorite keywords ranking update for user {user_id} after adding keywords: {e_rank}",
                        exc_info=True)

        return preference

    except Exception as e:
        raise


def delete_favorite_keywords(
        user_id,
        keywords_to_delete: list[str]) -> UserPreference:
    if not user_id or not keywords_to_delete:
        raise ValueError(
            "User ID and keywords list to delete cannot be empty.")

    try:
        with transaction.atomic():
            try:
                preference = UserPreference.objects.get(user_id=user_id)
            except UserPreference.DoesNotExist:
                return UserPreference(user_id=user_id, favorite_keywords=[])

            current_keywords = preference.favorite_keywords or []
            if not isinstance(current_keywords, list):
                current_keywords = []
                preference.favorite_keywords = []
            keywords_to_delete_lower = {kw.lower()
                                        for kw in keywords_to_delete}

            updated_keywords = []
            keywords_were_deleted = False
            for kw in current_keywords:
                if kw.lower() not in keywords_to_delete_lower:
                    updated_keywords.append(kw)
                else:
                    keywords_were_deleted = True

            if keywords_were_deleted:
                preference.favorite_keywords = updated_keywords
                preference.save(
                    update_fields=[
                        'favorite_keywords',
                        'updated_at'])
                # Trigger ranking update
                try:
                    update_user_favorite_keywords_rankings(user_id=user_id)
                except Exception as e_rank:
                    logger.error(
                        f"Error triggering summary favorite keywords ranking update for user {user_id} after deleting keywords: {e_rank}",
                        exc_info=True)

        return preference

    except Exception as e:
        raise
