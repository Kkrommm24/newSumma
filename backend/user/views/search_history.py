import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from user.serializers.serializers import UserSearchHistorySerializer, DeleteSearchHistorySerializer, AddSearchHistorySerializer
from user.services.search_history_service import get_user_search_history, add_user_search_history, delete_search_histories

logger = logging.getLogger(__name__)

class UserSearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            histories = get_user_search_history(user.id)
            serializer = UserSearchHistorySerializer(histories, many=True)
            return Response({
                "items": serializer.data,
                "status": "success"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": str(e),
                "items": [],
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        user = request.user
        
        serializer = AddSearchHistorySerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            try:
                new_history = add_user_search_history(user.id, query)
                output_serializer = UserSearchHistorySerializer(new_history)
                return Response({
                    "items": [output_serializer.data],
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except ValueError as ve:
                return Response({
                    "error": str(ve),
                    "items": [],
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "error": str(e),
                    "items": [],
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "error": serializer.errors,
                "items": [],
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user

        input_serializer = DeleteSearchHistorySerializer(data=request.data)
        if input_serializer.is_valid():
            queries = input_serializer.validated_data['queries']
            try:
                deleted_count = delete_search_histories(user.id, queries)
                
                if deleted_count > 0:
                    remaining_histories = get_user_search_history(user.id)
                    serializer = UserSearchHistorySerializer(remaining_histories, many=True)
                    return Response({
                        "items": serializer.data,
                        "status": "success"
                    }, status=status.HTTP_200_OK) 
                else:
                    return Response({
                        "error": "No matching search history entries found to delete.",
                        "items": [],
                        "status": "error"
                    }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    "error": str(e),
                    "items": [],
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "error": input_serializer.errors,
                "items": [],
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)