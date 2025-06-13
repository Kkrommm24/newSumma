import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from user.serializers.serializers import RequestPasswordResetSerializer, SetNewPasswordSerializer
from user.tasks import send_password_reset_email
from user.user.password_reset_controller.password_reset_controller import PasswordResetController

logger = logging.getLogger(__name__)
User = get_user_model()


class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            reset_token_str = PasswordResetController.generate_reset_token(
                user)
            logger.info(f"Generated reset token for user {user.email}")

            frontend_url = getattr(
                settings,
                'FRONTEND_RESET_PASSWORD_URL',
                'http://example.com/reset-password')
            reset_link = f"{frontend_url}/{reset_token_str}/"

            send_password_reset_email.delay(user.email, reset_link)

            return Response(
                {'message': 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.'},
                status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'message': 'Nếu email tồn tại trong hệ thống, bạn sẽ nhận được link đặt lại mật khẩu.'},
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
                payload = PasswordResetController.verify_reset_token(
                    reset_token_str)
                user_id = payload.get('user_id')

                try:
                    user = User.objects.get(pk=user_id)
                    logger.info(f"Found user with ID: {user_id}")
                except User.DoesNotExist:
                    logger.error(f"User not found with ID: {user_id}")
                    raise User.DoesNotExist

                tokens = PasswordResetController.reset_password(user, password)
                logger.info(
                    f"Successfully reset password for user: {user.email}")

                return Response({
                    'message': 'Đặt lại mật khẩu thành công.',
                    'detail': 'Vui lòng đăng nhập lại với mật khẩu mới.',
                    'access': tokens['access'],
                    'refresh': tokens['refresh']
                }, status=status.HTTP_200_OK)

            except ValueError as e:
                logger.error(f"Token validation error: {str(e)}")
                return Response({'error': str(e)},
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
