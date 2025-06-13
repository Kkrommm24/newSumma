from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from ..serializers.serializers import UserRegistrationSerializer
from rest_framework.exceptions import ValidationError

# Import controller
from user.user.user_registration_controller.user_registration_controller import UserRegistrationController
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            error_detail = e.detail
            is_conflict = False

            # Kiểm tra lỗi unique bằng `code` thay vì message string
            for field, errors in error_detail.items():
                if isinstance(errors, list) and any(getattr(msg, 'code', None) == 'unique' for msg in errors):
                    is_conflict = True
                    break
            
            if is_conflict:
                logger.warning(
                    f"UserRegistrationView: Conflict error during registration: {error_detail}")
                return Response(error_detail, status=status.HTTP_409_CONFLICT)
            else:
                logger.warning(
                    f"UserRegistrationView: Validation error during registration: {error_detail}")
                return Response(
                    error_detail,
                    status=status.HTTP_400_BAD_REQUEST)

        try:

            user = UserRegistrationController.register_user(
                serializer.validated_data)

            response_serializer = UserRegistrationSerializer(user)
            user_data = response_serializer.data
            user_data.pop('password', None)
            user_data.pop('password2', None)

            logger.info(
                f"UserRegistrationView: User {user.username} registered successfully.")
            return Response({
                "user": user_data,
                "message": "User registered successfully. Welcome email is being sent."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(
                f"UserRegistrationView: Unexpected error during registration: {e}",
                exc_info=True)
            return Response(
                {"error": "An unexpected error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
