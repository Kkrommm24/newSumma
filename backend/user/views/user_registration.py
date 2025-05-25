from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from ..serializers.serializers import UserRegistrationSerializer
from ..tasks import send_welcome_email_task
from rest_framework.exceptions import ValidationError

User = get_user_model()


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
            if 'email' in error_detail and any(
                    'already exists' in str(msg) for msg in error_detail['email']):
                is_conflict = True
            if 'username' in error_detail and any(
                    'already exists' in str(msg) for msg in error_detail['username']):
                is_conflict = True

            if is_conflict:
                return Response(error_detail, status=status.HTTP_409_CONFLICT)
            else:
                return Response(
                    error_detail,
                    status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except Exception as e:
            print(f"Error saving user: {e}")
            return Response(
                {
                    "error": "An unexpected error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        send_welcome_email_task.apply_async(
            args=[str(user.id)], queue='high_priority')

        user_data = UserRegistrationSerializer(
            user, context=self.get_serializer_context()).data
        user_data.pop('password', None)
        user_data.pop('password2', None)

        return Response({
            "user": user_data,
            "message": "User registered successfully. Welcome email is being sent via high priority queue."
        }, status=status.HTTP_201_CREATED)
