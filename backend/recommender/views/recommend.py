from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from recommender.services.recommend_service import (
    get_recommendations_for_user
)
from summarizer.serializers.serializers import (
    SummarySerializer as NewsAppSummarySerializer
)
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_recommendations(request):
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        current_summary_id = request.GET.get('current_summary_id')
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))

        summaries, articles_dict, source_info = get_recommendations_for_user(
            user_id,
            current_summary_id,
            limit=limit,
            offset=offset
        )

        serialized_summaries = []
        for summary in summaries:
            try:
                serializer_context = {
                    'request': request,
                    'articles': articles_dict
                }
                summary_data = NewsAppSummarySerializer(
                    summary, context=serializer_context).data
                serialized_summaries.append(summary_data)

            except Exception as e:
                continue

        response_data = {
            "summaries": serialized_summaries,
            "source": source_info,
            "total_count": source_info.get('total_count', 0),
            "has_more": source_info.get('has_more', False)
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
