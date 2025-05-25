import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from datetime import timedelta, datetime, timezone
import jwt

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import UntypedToken, TokenError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from user.serializers.serializers import RequestPasswordResetSerializer, SetNewPasswordSerializer
from user.tasks import send_password_reset_email

logger = logging.getLogger(__name__)

User = get_user_model()

# Thời gian token reset hợp lệ (5 phút)
PASSWORD_RESET_JWT_LIFETIME = timedelta(minutes=5)


class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Tạo payload cho token
            payload = {
                'user_id': str(
                    user.pk),
                'exp': datetime.now(
                    timezone.utc) +
                PASSWORD_RESET_JWT_LIFETIME,
                'token_type': 'password_reset'}

            # Ký token với secret key
            reset_token_str = jwt.encode(
                payload, settings.SECRET_KEY, algorithm='HS256')
            logger.info(f"Generated reset token for user {user.email}")

            frontend_url = getattr(
                settings,
                'FRONTEND_RESET_PASSWORD_URL',
                'http://example.com/reset-password')
            reset_link = f"{frontend_url}/{reset_token_str}/"

            send_password_reset_email.delay(user.email, reset_link)

            return Response(
                {
                    'message': 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.'},
                status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {
                    'message': 'Nếu email tồn tại trong hệ thống, bạn sẽ nhận được link đặt lại mật khẩu.'},
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi khi tạo token reset mật khẩu: {str(e)}")
            return Response({'error': 'Đã xảy ra lỗi khi xử lý yêu cầu.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            password = serializer.validated_data['password']
            reset_token_str = serializer.validated_data['reset_token']

            logger.info(
                f"Attempting to reset password with token: {reset_token_str[:10]}...")

            try:
                payload = jwt.decode(
                    reset_token_str,
                    settings.SECRET_KEY,
                    algorithms=['HS256'])
                logger.info(f"Successfully decoded token payload: {payload}")

                if payload.get('token_type') != 'password_reset':
                    logger.error("Invalid token type in payload")
                    raise InvalidToken(
                        "Token không phải loại dùng để đặt lại mật khẩu.")

                user_id = payload.get('user_id')
                if not user_id:
                    logger.error("No user_id in token payload")
                    raise InvalidToken(
                        "Token không chứa thông tin người dùng.")

                try:
                    user = User.objects.get(pk=user_id)
                    logger.info(f"Found user with ID: {user_id}")
                except User.DoesNotExist:
                    logger.error(f"User not found with ID: {user_id}")
                    raise User.DoesNotExist

                # Đặt lại mật khẩu và cập nhật thời gian
                user.set_password(password)
                user.save()
                logger.info(
                    f"Successfully reset password for user: {user.email}")

                # Xóa tất cả token cũ của user
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                tokens = OutstandingToken.objects.filter(user_id=user.id)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                tokens.delete()
                logger.info(
                    f"Blacklisted and deleted old tokens for user: {user.email}")

                # Tạo token mới
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)
                logger.info(f"Generated new tokens for user: {user.email}")

                return Response({
                    'message': 'Đặt lại mật khẩu thành công.',
                    'detail': 'Vui lòng đăng nhập lại với mật khẩu mới.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }, status=status.HTTP_200_OK)

            except jwt.ExpiredSignatureError:
                logger.error("Token has expired")
                return Response(
                    {'error': 'Liên kết đặt lại mật khẩu đã hết hạn.'}, status=status.HTTP_400_BAD_REQUEST)
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid token error: {str(e)}")
                return Response(
                    {
                        'error': f'Liên kết đặt lại mật khẩu không hợp lệ: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            logger.error(f"User not found for password reset")
            return Response({'error': 'Người dùng không tồn tại.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    error_messages = []
                    for field, errors in e.detail.items():
                        if isinstance(errors, list):
                            error_messages.extend(errors)
                        else:
                            error_messages.append(str(errors))
                    return Response({'error': error_messages[0] if error_messages else str(
                        e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'error': str(e.detail)},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
