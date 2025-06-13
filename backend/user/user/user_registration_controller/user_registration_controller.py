from user.services.registration_service import RegistrationService
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from user.models import User


class UserRegistrationController:
    @staticmethod
    def register_user(validated_data: Dict[str, Any]) -> 'User':
        return RegistrationService.register_user(validated_data)
