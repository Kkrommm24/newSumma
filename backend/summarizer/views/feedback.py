import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from summarizer.summarizers.feedback_controller import feedback_controller
from summarizer.summarizers.llama.tasks import summarize_single_article_task
from news.models import NewsArticle
from summarizer.models import NewsSummary

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_summary_feedback(request):
    summary_id = request.data.get('summary_id')
    is_upvote_input = request.data.get('is_upvote')
    user = request.user

    if not summary_id:
        return Response({'status': 'error',
                         'message': 'summary_id is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    is_upvote = None
    if is_upvote_input is True:
        is_upvote = True
    elif is_upvote_input is False:
        is_upvote = False

    try:
        summary_obj, trigger_resummarize, final_upvotes, final_downvotes = feedback_controller.record_feedback_interface(
            user=user, summary_id=summary_id, is_upvote=is_upvote)

        if summary_obj is None:
            try:
                NewsSummary.objects.get(id=summary_id)
                return Response(
                    {
                        'status': 'error',
                        'message': 'An internal server error occurred while processing feedback.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except NewsSummary.DoesNotExist:
                return Response({'status': 'error',
                                 'message': 'Summary not found.'},
                                status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(
                    f"View: Unexpected error checking summary existence for {summary_id}: {e}")
                return Response({'status': 'error',
                                 'message': 'An unexpected error occurred.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        article_published_at = None
        if summary_obj and summary_obj.article_id:
            try:
                article = NewsArticle.objects.get(id=summary_obj.article_id)
                article_published_at = article.published_at
            except NewsArticle.DoesNotExist:
                logger.warning(
                    f"View: Không tìm thấy NewsArticle với ID {summary_obj.article_id} cho summary {summary_obj.id}")
            except Exception as e:
                logger.exception(
                    f"View: Lỗi khi lấy NewsArticle {summary_obj.article_id} cho summary {summary_obj.id}: {e}")

        if trigger_resummarize:
            try:
                summarize_single_article_task.delay(
                    article_id_str=str(summary_obj.article_id))
            except Exception as task_error:
                logger.error(
                    f"View: Lỗi khi trigger summarize_single_article_task cho article {summary_obj.article_id}: {task_error}")
                pass

        return Response({
            'status': 'success',
            'message': 'Feedback recorded successfully.',
            'summary_id': summary_obj.id,
            'upvotes': final_upvotes,
            'downvotes': final_downvotes,
            'user_vote': is_upvote,
            'published_at': article_published_at
        }, status=status.HTTP_200_OK)

    except NewsSummary.DoesNotExist:
        return Response({'status': 'error',
                         'message': 'Summary not found.'},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(
            f"View: Unexpected error in record_summary_feedback for summary {summary_id}: {e}",
            exc_info=False)
        return Response({'status': 'error',
                         'message': 'An unexpected error occurred in the view.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
