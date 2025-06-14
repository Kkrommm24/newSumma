from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from user.serializers.serializers import UserPreferenceSerializer, AddFavoriteKeywordsSerializer, DeleteFavoriteKeywordsSerializer
from user.user.user_preference_controller.user_preference_controller import UserPreferenceController


class UserFavoriteKeywordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            preference = UserPreferenceController.get_user_preference(user.id)
            serializer = UserPreferenceSerializer(preference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'favorite_keywords': []},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching favorite keywords."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, *args, **kwargs):
        user = request.user
        input_serializer = AddFavoriteKeywordsSerializer(data=request.data)
        if input_serializer.is_valid():
            keywords = input_serializer.validated_data['keywords']
            try:
                updated_preference = UserPreferenceController.add_favorite_keywords(
                    user.id, keywords)
                output_serializer = UserPreferenceSerializer(
                    updated_preference)
                return Response(
                    output_serializer.data,
                    status=status.HTTP_200_OK)
            except ValueError as ve:
                return Response({"error": str(ve)},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": "An error occurred while updating favorite keywords."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        input_serializer = DeleteFavoriteKeywordsSerializer(data=request.data)
        if input_serializer.is_valid():
            keywords = input_serializer.validated_data['keywords']
            try:
                updated_preference = UserPreferenceController.delete_favorite_keywords(
                    user.id, keywords)
                output_serializer = UserPreferenceSerializer(
                    updated_preference)
                return Response(
                    output_serializer.data,
                    status=status.HTTP_200_OK)
            except ValueError as ve:
                return Response({"error": str(ve)},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": "An error occurred while deleting favorite keywords."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)
