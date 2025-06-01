from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from summarizer.models import NewsSummary
from summarizer.serializers.serializers import SummarySerializer
from summarizer.services.article_service import ArticleService
from summarizer.summarizers.llama.tasks import generate_article_summaries, summarize_single_article_task
import logging
from news.utils.summary_utils import get_articles_for_summaries

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_summaries(request):
    try:
        article_id_param = request.GET.get('article_id')
        sort_by = request.GET.get('sort_by', '-created_at')

        queryset = NewsSummary.objects.all()

        if article_id_param:
            queryset = queryset.filter(article_id=article_id_param)

        valid_sort_fields = [
            'created_at', '-created_at',
            'upvotes', '-upvotes',
            'downvotes', '-downvotes',
        ]
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

        paginator = StandardResultsSetPagination()
        paginated_summaries = paginator.paginate_queryset(queryset, request)

        articles_dict = get_articles_for_summaries(paginated_summaries)

        # Truyền thêm request vào context
        serializer_context = {
            'articles': articles_dict,
            'request': request
        }
        serializer = SummarySerializer(
            paginated_summaries,
            many=True,
            context=serializer_context)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': 'ERROR',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def trigger_bulk_summarization(request):
    try:
        limit = request.data.get('limit', 10)
        task = generate_article_summaries.delay(limit=limit)
        return Response(
            {
                'status': 'queued',
                'message': f'Yêu cầu tóm tắt cho tối đa {limit} bài viết đã được đưa vào hàng đợi.',
                'task_id': task.id},
            status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': 'Không thể đưa yêu cầu tóm tắt vào hàng đợi.',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def trigger_single_summarization(request, article_pk):
    article_service = ArticleService()

    try:
        article_exists = article_service.check_article_exists(article_pk)
        if not article_exists:
            return Response({'status': 'error',
                             'message': 'Article not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        article_id_str = str(article_pk)
        task = summarize_single_article_task.delay(
            article_id_str=article_id_str)

        return Response(
            {
                'status': 'queued',
                'message': f'Yêu cầu tóm tắt cho bài viết {article_id_str} đã được đưa vào hàng đợi.',
                'task_id': task.id},
            status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': 'Không thể đưa yêu cầu tóm tắt vào hàng đợi.',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
