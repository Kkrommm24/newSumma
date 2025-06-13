from user.services import registration_service
import logging

logger = logging.getLogger(__name__)

def register_user_interface(validated_data):
    try:
        user = registration_service.register_user(validated_data)
        return user
    except Exception as e:
        logger.error(f"UserRegistrationController: Error during user registration: {e}", exc_info=False)
        raise
