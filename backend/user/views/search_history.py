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
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching SearchHistory for user {user.id}: {e}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching search history."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"POST request received for user {user.id} search history, data: {request.data}")
        
        serializer = AddSearchHistorySerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            try:
                new_history = add_user_search_history(user.id, query)
                output_serializer = UserSearchHistorySerializer(new_history)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as ve:
                logger.warning(f"Validation error adding search history for user {user.id}: {ve}")
                return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Error creating SearchHistory for user {user.id}: {e}", exc_info=True)
                return Response(
                    {"error": "An error occurred while saving search history."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"Invalid input for adding search history for user {user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"DELETE request received for user {user.id} search history, data: {request.data}")

        input_serializer = DeleteSearchHistorySerializer(data=request.data)
        if input_serializer.is_valid():
            queries = input_serializer.validated_data['queries']
            try:
                deleted_count = delete_search_histories(user.id, queries)
                
                if deleted_count > 0:
                    remaining_histories = get_user_search_history(user.id)
                    serializer = UserSearchHistorySerializer(remaining_histories, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK) 
                else:
                    logger.info(f"No matching search history found to delete for user {user.id}. Queries: {queries}")
                    return Response(
                        {"detail": "No matching search history entries found to delete."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                logger.error(f"Error deleting search history for user {user.id}: {e}", exc_info=True)
                return Response(
                    {"error": "An error occurred while deleting search history."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"Invalid input for deleting search history for user {user.id}: {input_serializer.errors}")
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)