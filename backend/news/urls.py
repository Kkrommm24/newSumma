from django.urls import path
from .views.summary import SummaryDetailView, ArticleSummaryView
from .views.comment import CommentListCreateView, CommentDetailView

urlpatterns = [
    path(
        'summaries/<uuid:id>/',
        SummaryDetailView.as_view(),
        name='summary-detail'),
    path(
        'articles/<uuid:article_id>/summary/',
        ArticleSummaryView.as_view(),
        name='article-summary'),
    path(
        'summaries/<uuid:summary_id>/comments/',
        CommentListCreateView.as_view(),
        name='summary-comments'),
    path(
        'comments/<uuid:id>/',
        CommentDetailView.as_view(),
        name='comment-detail'),
]
