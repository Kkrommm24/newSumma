import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from summarizer.services.feedback_service import FeedbackService
from summarizer.summarizers.llama.tasks import summarize_single_article_task
from news.models import NewsSummary

logger = logging.getLogger(__name__)

feedback_service = FeedbackService()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_summary_feedback(request):
    summary_id = request.data.get('summary_id')
    is_upvote_input = request.data.get('is_upvote')
    user = request.user

    if not summary_id:
        return Response({'status': 'error', 'message': 'summary_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if is_upvote_input is None or not isinstance(is_upvote_input, bool):
        return Response({'status': 'error', 'message': 'is_upvote (boolean) is required.'}, status=status.HTTP_400_BAD_REQUEST)

    is_upvote = bool(is_upvote_input)

    try:
        summary_obj, trigger_resummarize, final_upvotes, final_downvotes = feedback_service.record_feedback_and_check_threshold(
            user=user,
            summary_id=summary_id,
            is_upvote=is_upvote
        )

        if summary_obj is None:
            try:
                NewsSummary.objects.get(id=summary_id)
                return Response({'status': 'error', 'message': 'An internal server error occurred while processing feedback.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except NewsSummary.DoesNotExist:
                 return Response({'status': 'error', 'message': 'Summary not found.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.exception(f"View: Lỗi khi kiểm tra lại summary {summary_id}: {e}")
                return Response({'status': 'error', 'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if trigger_resummarize:
            try:
                summarize_single_article_task.delay(article_id_str=str(summary_obj.article_id))
                logger.info(f"View: Đã gửi yêu cầu tóm tắt lại cho bài viết {summary_obj.article_id} vào hàng đợi.")
            except Exception as task_error:
                logger.error(f"View: Lỗi khi gửi task tóm tắt lại từ view cho bài viết {summary_obj.article_id}: {task_error}", exc_info=True)
                pass

        return Response({
            'status': 'success',
            'message': 'Feedback recorded successfully.',
            'summary_id': summary_obj.id,
            'upvotes': final_upvotes,
            'downvotes': final_downvotes,
            'user_vote': is_upvote
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"View: Lỗi không mong muốn khi xử lý feedback cho summary {summary_id}: {e}")
        return Response({'status': 'error', 'message': 'An unexpected error occurred in the view.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 