from rest_framework import status
from rest_framework.exceptions import APIException
from user.services.auth_service import AuthService
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from user.models import User

class AuthException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Đã xảy ra lỗi khi xử lý xác thực.'
    default_code = 'auth_error'


class AuthController:
    @staticmethod
    def change_password(user: 'User', new_password: str):
        try:
            AuthService.change_password(user, new_password)
        except Exception as e:
            raise AuthException(f"Lỗi khi đổi mật khẩu: {str(e)}")

    @staticmethod
    def delete_account(user: 'User'):
        try:
            return AuthService.deactivate_user(user)
        except Exception as e:
            raise AuthException(f"Lỗi khi xóa tài khoản: {str(e)}")
