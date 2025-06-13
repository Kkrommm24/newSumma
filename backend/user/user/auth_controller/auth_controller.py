from rest_framework import status
from rest_framework.exceptions import APIException
from user.services.auth_service import AuthService


class AuthException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Đã xảy ra lỗi khi xử lý xác thực.'
    default_code = 'auth_error'


class AuthController:
    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str):
        try:
            user = AuthService.get_user_by_id(user_id)
            if not AuthService.verify_password(user, old_password):
                raise ValueError("Mật khẩu hiện tại không đúng.")

            AuthService.change_password(user, new_password)
            return True
        except ValueError as e:
            raise AuthException(str(e))
        except Exception as e:
            raise AuthException(f"Lỗi khi đổi mật khẩu: {str(e)}")

    @staticmethod
    def delete_account(user_id: str, password: str):
        try:
            user = AuthService.get_user_by_id(user_id)
            if not AuthService.verify_password(user, password):
                raise ValueError("Mật khẩu không đúng.")

            return AuthService.deactivate_user(user)
        except ValueError as e:
            raise AuthException(str(e))
        except Exception as e:
            raise AuthException(f"Lỗi khi xóa tài khoản: {str(e)}")
