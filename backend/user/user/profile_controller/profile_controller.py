from user.services import profile_service
import logging

logger = logging.getLogger(__name__)

def get_user_profile_interface(user_id):
    try:
        return profile_service.get_user_profile(user_id)
    except Exception as e:
        logger.error(f"ProfileController: Error in get_user_profile for user_id {user_id}: {e}", exc_info=True)
        raise

def update_user_profile_interface(user_id, validated_data, avatar_file=None):
    try:
        return profile_service.update_user_profile(user_id, validated_data, avatar_file)
    except ValueError as ve:
        logger.warning(f"ProfileController: ValueError in update_user_profile for user_id {user_id}: {ve}")
        raise
    except Exception as e:
        logger.error(f"ProfileController: Error in update_user_profile for user_id {user_id}: {e}", exc_info=True)
        raise

def delete_user_profile_interface(user_id):
    try:
        return profile_service.delete_user_profile(user_id)
    except Exception as e:
        logger.error(f"ProfileController: Error in delete_user_profile for user_id {user_id}: {e}", exc_info=True)
        raise
