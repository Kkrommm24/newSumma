from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from summarizer.models import NewsSummary

from recommender.recommenders.recommender_controller.recommender_controller import (
    log_summary_view_interface, track_source_click_interface)
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def log_summary_view_time(request):
    summary_id = request.data.get('summary_id')
    duration_seconds_str = request.data.get('duration_seconds')

    if not summary_id:
        return Response({"error": "Summary ID is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    if not duration_seconds_str:  # Ensure it's not None or empty
        return Response({"error": "Duration seconds is required"},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        duration_seconds = int(duration_seconds_str)
        if duration_seconds < 0:
            return Response({"error": "Duration must be a non-negative integer."},
                            status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):  # Catch if duration_seconds_str is not a valid int string
        return Response(
            {
                "error": "Invalid duration_seconds format. Must be an integer."},
            status=status.HTTP_400_BAD_REQUEST)

    user = request.user if request.user.is_authenticated else None
    user_id = user.id if user else None

    try:
        total_duration = log_summary_view_interface(
            user_id=user_id,
            summary_id=summary_id,
            duration_seconds=duration_seconds
        )

        return Response({
            "message": "View time logged successfully.",
            "total_duration": total_duration
        }, status=status.HTTP_201_CREATED)

    except NewsSummary.DoesNotExist:
        return Response({"error": "Summary not found"},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(
            f"Failed to log view time for summary {summary_id}, user {user_id}: {e}",
            exc_info=True)
        return Response({"error": "Failed to log view time due to a server error."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def track_source_click(request):
    summary_id_from_request = request.data.get('summary_id')
    if not summary_id_from_request:
        return Response({"error": "Summary ID is required"},
                        status=status.HTTP_400_BAD_REQUEST)

    current_user = request.user if request.user.is_authenticated else None
    user_id_to_log = current_user.id if current_user else None

    try:
        service_response = track_source_click_interface(
            user_id_to_log,
            summary_id_from_request
        )

        return Response({
            "message": "Click tracked and processed.",
            "details": service_response.get("message")
        }, status=status.HTTP_201_CREATED)

    except NewsSummary.DoesNotExist:
        return Response({"error": "Summary not found"},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(
            f"Failed to track click for summary {summary_id_from_request}, user {user_id_to_log}: {e}",
            exc_info=True)
        return Response({"error": "Failed to track click due to a server error."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
