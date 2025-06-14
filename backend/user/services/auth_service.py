from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from user.models import User

User = get_user_model()


class AuthService:
    @staticmethod
    def get_user_by_id(user_id: str) -> 'User':
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("Không tìm thấy người dùng.")

    @staticmethod
    def get_user_by_email(email: str) -> 'User':
        try:
            return User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(
                "Không tìm thấy người dùng với email này.")

    @staticmethod
    def verify_password(user: 'User', password: str) -> bool:
        return user.check_password(password)

    @staticmethod
    def change_password(user: 'User', new_password: str):
        user.set_password(new_password)
        user.save()

    @staticmethod
    def deactivate_user(user: 'User'):
        if not user.is_active:
            return True
        user.is_active = False
        user.save(update_fields=['is_active'])
        return True
