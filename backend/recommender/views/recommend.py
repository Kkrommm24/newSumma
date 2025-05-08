from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from recommender.services.recommend_service import get_recommendations_for_user

from news.utils.pagination import InfiniteScrollPagination
from news.serializers.serializers import SummarySerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommended_articles(request):
    user_id = request.user.id
    if not user_id:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        final_summaries, articles_dict, _ = get_recommendations_for_user(user_id)


        paginator = InfiniteScrollPagination()
        paginated_summaries = paginator.paginate_queryset(final_summaries, request, view=None)

        serializer_context = {
            'articles': articles_dict,
            'request': request
        }
        
        serializer = SummarySerializer(paginated_summaries, many=True, context=serializer_context)
        
        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        logger.error(f"❌ Lỗi API khi lấy gợi ý cho user {user_id}: {e}")
        return Response({"error": "Failed to fetch recommendations"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
