from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from user.user.profile_controller import profile_controller
from user.serializers.serializers import UserProfileUpdateSerializer
import logging

logger = logging.getLogger(__name__)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user_id = request.user.id
        try:
            profile_data = profile_controller.get_user_profile_interface(user_id)
            if profile_data:
                return Response(profile_data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Không tìm thấy người dùng."},
                                status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"UserProfileView: Error in GET for user {user_id}: {e}", exc_info=True)
            return Response({"error": "Đã xảy ra lỗi khi lấy thông tin hồ sơ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(
            user, data=request.data, partial=True)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            avatar_file = request.FILES.get('avatar')

            try:
                updated_profile = profile_controller.update_user_profile_interface(
                    user.id, validated_data, avatar_file)
                if updated_profile:
                    return Response(updated_profile, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"error": "Không thể cập nhật hồ sơ. Người dùng không tồn tại hoặc có lỗi khác."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"UserProfileView: Error in PUT for user {user.id}: {e}", exc_info=True)
                return Response({"error": "Đã xảy ra lỗi trong quá trình cập nhật."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_id = request.user.id
        try:
            success = profile_controller.delete_user_profile_interface(user_id)
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"error": "Không tìm thấy người dùng để xóa."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"UserProfileView: Error in DELETE for user {user_id}: {e}", exc_info=True)
            return Response({"error": "Đã xảy ra lỗi khi xóa hồ sơ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
