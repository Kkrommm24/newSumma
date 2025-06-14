from django.urls import path
from .views.comment import CommentListCreateView, CommentDetailView

urlpatterns = [
    path(
        'summaries/<uuid:summary_id>/comments/',
        CommentListCreateView.as_view(),
        name='summary-comments'),
    path(
        'comments/<uuid:id>/',
        CommentDetailView.as_view(),
        name='comment-detail'),
]
