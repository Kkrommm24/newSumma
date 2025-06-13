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
        if serializer.is_valid():
            user_id = request.user.id
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            try:
                success = AuthController.change_password(
                    user_id, old_password, new_password)
                if success:
                    return Response(
                        {"message": "Đổi mật khẩu thành công."},
                        status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountDeletionSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            user_id = request.user.id

            try:
                success = AuthController.delete_account(user_id, password)
                if success:
                    return Response(
                        {"message": "Tài khoản đã được vô hiệu hóa."},
                        status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)
