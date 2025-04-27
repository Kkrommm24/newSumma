from rest_framework import generics, status, permissions
from rest_framework.response import Response
from user.serializers.serializers import (
    UserBookmarkSerializer, 
    AddBookmarkSerializer, 
    DeleteBookmarkSerializer
)
from user.services import bookmark_service
from rest_framework.exceptions import APIException

class UserBookmarkView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddBookmarkSerializer
        elif self.request.method == 'DELETE':
            return DeleteBookmarkSerializer
        return UserBookmarkSerializer

    def get(self, request, *args, **kwargs):
        try:
            user_id = request.user.id
            bookmarks = bookmark_service.get_bookmarks(user_id)
            serializer = UserBookmarkSerializer(bookmarks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except APIException as e:
            return Response({"detail": e.detail}, status=e.status_code)
        except Exception as e:
            return Response({"detail": "Lỗi hệ thống khi lấy bookmark."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        serializer = AddBookmarkSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_id = request.user.id
                article_id = serializer.validated_data['article_id']
                bookmark_service.add_bookmark(user_id, article_id)
                return Response({"detail": "Bookmark đã được thêm thành công."}, status=status.HTTP_201_CREATED)
            except APIException as e:
                return Response({"detail": e.detail}, status=e.status_code)
            except Exception as e:
                return Response({"detail": "Lỗi hệ thống khi thêm bookmark."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        serializer = DeleteBookmarkSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_id = request.user.id
                article_id = serializer.validated_data['article_id']
                bookmark_service.remove_bookmark(user_id, article_id)
                return Response({"detail": "Bookmark đã được xóa thành công."}, status=status.HTTP_200_OK)
            except APIException as e:
                return Response({"detail": e.detail}, status=e.status_code)
            except Exception as e:
                return Response({"detail": "Lỗi hệ thống khi xóa bookmark."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
