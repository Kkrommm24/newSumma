import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from datetime import timedelta, datetime, timezone

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
            
            token = UntypedToken() 
            token.payload['user_id'] = str(user.pk)
            token.payload['exp'] = datetime.now(timezone.utc) + PASSWORD_RESET_JWT_LIFETIME

            token.payload['token_type'] = 'password_reset' 
            reset_token_str = str(token)

            frontend_url = getattr(settings, 'FRONTEND_RESET_PASSWORD_URL', 'http://example.com/reset-password') 
            # Link giờ chỉ chứa token
            reset_link = f"{frontend_url}/{reset_token_str}/"

            send_password_reset_email.delay(user.email, reset_link)

            return Response({'message': 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
             return Response({'message': 'Nếu email tồn tại trong hệ thống, bạn sẽ nhận được link đặt lại mật khẩu.'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log lỗi
            print(f"Error generating password reset token: {e}") 
            return Response({'error': 'Đã xảy ra lỗi khi xử lý yêu cầu.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        password = serializer.validated_data['password']
        reset_token_str = serializer.validated_data['reset_token']
        user = None

        try:
            untyped_token = UntypedToken(reset_token_str)
            payload = untyped_token.payload
            
            if payload.get('token_type') != 'password_reset':
                raise InvalidToken("Token không phải loại dùng để đặt lại mật khẩu.") 

            user_id = payload.get('user_id')
            if not user_id:
                 raise InvalidToken("Token không chứa thông tin người dùng.")
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save(update_fields=['password'])

            print(f"--- PasswordResetConfirmView: Password saved successfully ---", flush=True) 
            return Response({'message': 'Đặt lại mật khẩu thành công.'}, status=status.HTTP_200_OK)

        except (InvalidToken, TokenError) as e:
             error_message = str(e) if str(e) else "Token không hợp lệ hoặc đã hết hạn."
             return Response({'error': f'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn: {error_message}'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
             return Response({'error': 'Người dùng không tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             return Response({'error': 'Đã xảy ra lỗi không mong muốn.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 