from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from crawler.crawlers.baomoi.tasks import crawl_baomoi_articles
from crawler.crawlers.vnexpress.tasks import crawl_vnexpress_articles
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
# @permission_classes([IsAdminUser]) # Chỉ admin mới được trigger crawl
def trigger_crawl_baomoi(request):
    """API POST để crawl Báo Mới sử dụng Celery task"""
    try:
        logger.info("View: Bắt đầu trigger crawl dữ liệu từ Báo Mới")
        task = crawl_baomoi_articles.delay()
        logger.info(f"View: Đã gửi task crawl Báo Mới với ID: {task.id}")
        return Response({
            'status': 'queued',
            'message': 'Đã gửi task crawl Báo Mới',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger.exception(f"View: Lỗi khi gửi task crawl Báo Mới: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Lỗi khi gửi task crawl Báo Mới',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
# @permission_classes([IsAdminUser]) # Chỉ admin mới được trigger crawl
def trigger_crawl_vnexpress(request):
    """API POST để crawl VnExpress sử dụng Celery task"""
    try:
        logger.info("View: Bắt đầu trigger crawl dữ liệu từ VnExpress")
        task = crawl_vnexpress_articles.delay()
        logger.info(f"View: Đã gửi task crawl VnExpress với ID: {task.id}")
        return Response({
            'status': 'queued',
            'message': 'Đã gửi task crawl VnExpress',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger.exception(f"View: Lỗi khi gửi task crawl VnExpress: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Lỗi khi gửi task crawl VnExpress',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
