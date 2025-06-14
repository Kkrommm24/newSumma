from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from user.serializers.serializers import PasswordChangeSerializer, AccountDeletionSerializer
from user.user.auth_controller.auth_controller import AuthController


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            AuthController.change_password(
                request.user, serializer.validated_data['new_password'])
            return Response(
                {"message": "Đổi mật khẩu thành công."},
                status=status.HTTP_200_OK)
        except Exception as e:
            error_data = e.detail if hasattr(e, 'detail') else str(e)
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountDeletionSerializer(
            data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            AuthController.delete_account(request.user)
            return Response(
                {"message": "Tài khoản đã được vô hiệu hóa."},
                status=status.HTTP_200_OK)
        except Exception as e:
            error_data = e.detail if hasattr(e, 'detail') else str(e)
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
