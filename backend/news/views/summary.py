from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status, viewsets
from news.models import NewsSummary, NewsArticle
from news.serializers.serializers import SummarySerializer
from news.summarizers.llama.article_summary import LlamaSummarizer
from django.db.models import Exists, OuterRef
import logging
import gc
import torch

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_summaries(request):
    """Lấy danh sách summary với các tùy chọn lọc"""
    try:
        article_id = request.GET.get('article_id')
        sort_by = request.GET.get('sort_by', '-created_at')

        queryset = NewsSummary.objects.all()

        if article_id:
            queryset = queryset.filter(article_id=article_id)
            
        queryset = queryset.order_by(sort_by)
        
        serializer = SummarySerializer(queryset, many=True)
        
        if not queryset.exists():
            return Response({
                'status': 'error',
                'message': 'NOT_FOUND',
                'results': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            'status': 'success',
            'message': 'SUCCESS',
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': 'ERROR',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ArticleSummaryViewSet(viewsets.ViewSet):
    """ViewSet cho việc tóm tắt bài viết"""
    summarizer = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.summarizer is None:
            self.summarizer = LlamaSummarizer()

    def get_object(self):
        """Lấy article theo ID"""
        article_id = self.kwargs.get('pk')
        try:
            return NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def _cleanup_memory(self):
        """Dọn dẹp bộ nhớ"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    @action(detail=False, methods=['post'])
    def summarize_articles_have_no_summaries(self, request):
        try:
            limit = request.data.get('limit', 5)  # Giảm limit mặc định xuống 5
            articles = NewsArticle.objects.filter(
                ~Exists(
                    NewsSummary.objects.filter(
                        article_id=OuterRef('id')
                    )
                )
            ).order_by('-published_at')[:limit]

            results = []
            for article in articles:
                try:
                    # Dọn dẹp bộ nhớ trước khi tóm tắt
                    self._cleanup_memory()
                    
                    summary_text = self.summarizer.summarize(article.content)
                    if summary_text:
                        summary = NewsSummary.objects.create(
                            article_id=article.id,
                            summary_text=summary_text,
                            upvotes=0,
                            downvotes=0
                        )
                        serializer = SummarySerializer(summary)
                        results.append(serializer.data)
                        logger.info(f"Đã tóm tắt thành công bài viết: {article.title}")
                except Exception as e:
                    logger.error(f"Lỗi khi tóm tắt bài viết {article.id}: {str(e)}")
                    results.append({
                        'article_id': str(article.id),
                        'error': str(e)
                    })
                    # Dọn dẹp bộ nhớ nếu có lỗi
                    self._cleanup_memory()

            return Response({
                'status': 'success',
                'message': f'Đã xử lý {len(results)} bài viết',
                'results': results
            })

        except Exception as e:
            logger.exception(f"Lỗi khi xử lý tóm tắt: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'ERROR',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def summarize_article_by_id(self, request, pk=None):
        try:
            article = self.get_object()
            
            # Dọn dẹp bộ nhớ trước khi tóm tắt
            self._cleanup_memory()
            
            summary_text = self.summarizer.summarize(article.content)
            
            if not summary_text:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Không thể tóm tắt bài viết'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Kiểm tra xem đã có summary chưa
            existing_summary = NewsSummary.objects.filter(article_id=article.id).first()
            if existing_summary:
                existing_summary.summary_text = summary_text
                existing_summary.save()
                summary = existing_summary
            else:
                summary = NewsSummary.objects.create(
                    article_id=article.id,
                    summary_text=summary_text,
                    upvotes=0,
                    downvotes=0
                )

            logger.info(f"Đã tóm tắt thành công bài viết: {article.title}")
            serializer = SummarySerializer(summary)
            
            # Dọn dẹp bộ nhớ sau khi hoàn thành
            self._cleanup_memory()
            
            return Response({
                'status': 'success',
                'message': 'SUCCESS',
                'results': serializer.data
            })

        except Exception as e:
            logger.exception(f"Lỗi khi tóm tắt bài viết: {str(e)}")
            # Dọn dẹp bộ nhớ nếu có lỗi
            self._cleanup_memory()
            return Response(
                {
                    'status': 'error',
                    'message': 'ERROR',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
