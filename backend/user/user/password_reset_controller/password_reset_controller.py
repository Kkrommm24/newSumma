from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta, datetime, timezone
import jwt
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework import status
from rest_framework.exceptions import APIException
from user.services.password_reset_service import PasswordResetService
from user.services.auth_service import AuthService

logger = logging.getLogger(__name__)
User = get_user_model()

PASSWORD_RESET_JWT_LIFETIME = timedelta(minutes=5)


class PasswordResetException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Đã xảy ra lỗi khi xử lý đặt lại mật khẩu.'
    default_code = 'password_reset_error'


class PasswordResetController:
    @staticmethod
    def generate_reset_token(user):
        try:
            return PasswordResetService.generate_reset_token(user)
        except Exception as e:
            raise PasswordResetException(
                f"Lỗi khi tạo token reset mật khẩu: {str(e)}")

    @staticmethod
    def verify_reset_token(token):
        try:
            return PasswordResetService.verify_reset_token(token)
        except ValueError as e:
            raise PasswordResetException(str(e))
        except Exception as e:
            raise PasswordResetException(f"Lỗi khi xác thực token: {str(e)}")

    @staticmethod
    def reset_password(user, new_password):
        try:
            return PasswordResetService.reset_password(user, new_password)
        except Exception as e:
            raise PasswordResetException(f"Lỗi khi đặt lại mật khẩu: {str(e)}")
