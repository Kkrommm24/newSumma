from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from user.serializers.serializers import PasswordChangeSerializer, AccountDeletionSerializer
from user.services.auth_service import change_user_password, delete_account_with_password
from django.core.exceptions import ObjectDoesNotExist


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
                success = change_user_password(
                    user_id, old_password, new_password)
                if success:
                    return Response(
                        {"message": "Đổi mật khẩu thành công."}, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                return Response(
                    {"error": "Không tìm thấy người dùng."}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({"error": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Lỗi không mong muốn khác
                print(f"Password change error: {e}")
                return Response({"error": "Đã xảy ra lỗi trong quá trình đổi mật khẩu."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                success = delete_account_with_password(user_id, password)
                if success:
                    return Response(
                        {"message": "Tài khoản đã được vô hiệu hóa."}, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                return Response(
                    {"error": "Không tìm thấy người dùng."}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({"error": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Account deletion error: {e}")
                return Response({"error": "Đã xảy ra lỗi trong quá trình xử lý."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)
