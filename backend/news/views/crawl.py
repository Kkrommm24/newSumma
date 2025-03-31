from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from news.crawlers.baomoi.tasks import crawl_baomoi_articles
from news.crawlers.vnexpress.tasks import crawl_vnexpress_articles
import logging

logger = logging.getLogger(__name__)

class CrawlerViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def baomoi(self, request):
        """API POST để crawl Báo Mới sử dụng Celery task"""
        try:
            logger.info("Bắt đầu crawl dữ liệu từ Báo Mới")
            # Gọi Celery task
            task = crawl_baomoi_articles.delay()
            
            logger.info(f"Đã gửi task crawl Báo Mới với ID: {task.id}")
            return Response({
                'status': 'success',
                'message': 'Đã gửi task crawl Báo Mới',
                'results': {
                    'task_id': task.id,
                    'status': 'PENDING'
                }
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logger.exception(f"Lỗi khi gửi task crawl Báo Mới: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Lỗi khi gửi task crawl Báo Mới',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def vnexpress(self, request):
        """API POST để crawl VnExpress sử dụng Celery task"""
        try:
            logger.info("Bắt đầu crawl dữ liệu từ VnExpress")
            # Gọi Celery task
            task = crawl_vnexpress_articles.delay()
            
            logger.info(f"Đã gửi task crawl VnExpress với ID: {task.id}")
            return Response({
                'status': 'success',
                'message': 'Đã gửi task crawl VnExpress',
                'results': {
                    'task_id': task.id,
                    'status': 'PENDING'
                }
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logger.exception(f"Lỗi khi gửi task crawl VnExpress: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Lỗi khi gửi task crawl VnExpress',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
