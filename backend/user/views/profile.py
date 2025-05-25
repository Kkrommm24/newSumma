from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from user.services.profile_service import get_user_profile, update_user_profile, delete_user_profile
from user.serializers.serializers import UserProfileUpdateSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user_id = request.user.id
        profile_data = get_user_profile(user_id)

        if profile_data:
            return Response(profile_data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Không tìm thấy người dùng."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            avatar_file = request.FILES.get('avatar')

            try:
                updated_profile = update_user_profile(user.id, validated_data, avatar_file)
                if updated_profile:
                    return Response(updated_profile, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Không thể cập nhật hồ sơ."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Error updating profile: {e}")
                return Response({"error": "Đã xảy ra lỗi trong quá trình cập nhật."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_id = request.user.id
        success = delete_user_profile(user_id)

        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Không tìm thấy người dùng để xóa."}, status=status.HTTP_404_NOT_FOUND) 