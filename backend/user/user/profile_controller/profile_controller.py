from user.services.profile_service import ProfileService
from typing import Dict, Optional, Any


class ProfileController:
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        return ProfileService.get_user_profile(user_id)

    @staticmethod
    def update_user_profile(user_id: str,
                            data: Dict[str,
                                       Any],
                            avatar_file: Optional[Any] = None) -> Optional[Dict[str,
                                                                                Any]]:
        return ProfileService.update_user_profile(user_id, data, avatar_file)

    @staticmethod
    def delete_user_profile(user_id: str) -> bool:
        return ProfileService.delete_user_profile(user_id)
