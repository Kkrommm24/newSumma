from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta, datetime, timezone
import jwt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from user.models import User

User = get_user_model()


class PasswordResetService:
    PASSWORD_RESET_JWT_LIFETIME = timedelta(minutes=5)

    @staticmethod
    def generate_reset_token(user: 'User') -> str:
        payload = {
            'user_id': str(
                user.pk),
            'exp': datetime.now(
                timezone.utc) +
            PasswordResetService.PASSWORD_RESET_JWT_LIFETIME,
            'token_type': 'password_reset'}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def verify_reset_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256'])
            if payload.get('token_type') != 'password_reset':
                raise ValueError(
                    "Token không phải loại dùng để đặt lại mật khẩu.")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Liên kết đặt lại mật khẩu đã hết hạn.")
        except jwt.InvalidTokenError as e:
            raise ValueError(
                f"Liên kết đặt lại mật khẩu không hợp lệ: {str(e)}")

    @staticmethod
    def reset_password(user: 'User', new_password: str) -> Dict[str, str]:
        user.set_password(new_password)
        user.save()

        # Xóa tất cả token cũ
        tokens = OutstandingToken.objects.filter(user_id=user.id)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        tokens.delete()

        # Tạo token mới
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
