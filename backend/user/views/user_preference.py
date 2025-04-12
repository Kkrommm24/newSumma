import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from news.models import UserPreference
from user.serializers.serializers import UserPreferenceSerializer, AddFavoriteKeywordsSerializer, DeleteFavoriteKeywordsSerializer
from user.services.user_preference_service import add_favorite_keywords, delete_favorite_keywords

logger = logging.getLogger(__name__)

class UserFavoriteKeywordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            preference = UserPreference.objects.get(user_id=user.id)
            serializer = UserPreferenceSerializer(preference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserPreference.DoesNotExist:
            logger.info(f"UserPreference not found for user {user.id}. Returning empty list.")
            return Response({'favorite_keywords': []}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching UserPreference for user {user.id}: {e}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching favorite keywords."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, *args, **kwargs):
        logger.info(f"PATCH request received for user {request.user.id}, data: {request.data}")
        user = request.user
        input_serializer = AddFavoriteKeywordsSerializer(data=request.data)
        if input_serializer.is_valid():
            keywords = input_serializer.validated_data['keywords']
            try:
                updated_preference = add_favorite_keywords(user.id, keywords)
                output_serializer = UserPreferenceSerializer(updated_preference)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            except ValueError as ve:
                logger.warning(f"Value error adding keywords for user {user.id}: {ve}")
                return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Error updating keywords for user {user.id}: {e}", exc_info=True)
                return Response(
                    {"error": "An error occurred while updating favorite keywords."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"Invalid input for adding keywords for user {user.id}: {input_serializer.errors}")
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"DELETE request received for user {user.id}, data: {request.data}")

        input_serializer = DeleteFavoriteKeywordsSerializer(data=request.data)
        if input_serializer.is_valid():
            keywords = input_serializer.validated_data['keywords']
            try:
                updated_preference = delete_favorite_keywords(user.id, keywords)
                output_serializer = UserPreferenceSerializer(updated_preference)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            except ValueError as ve:
                logger.warning(f"Value error deleting keywords for user {user.id}: {ve}")
                return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": "An error occurred while deleting favorite keywords."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"Invalid input for deleting keywords for user {user.id}: {input_serializer.errors}")
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)