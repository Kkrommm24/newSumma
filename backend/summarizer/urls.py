from django.urls import path
from summarizer.views.summary import get_summaries, trigger_bulk_summarization, trigger_single_summarization
from .views.search import ArticleSummarySearchView
from .views.feedback import record_summary_feedback

app_name = 'summarizer'

urlpatterns = [
    path(
        'summaries/',
        get_summaries,
        name='get-summaries'),
    path(
        'summaries/trigger-bulk/',
        trigger_bulk_summarization,
        name='trigger-bulk-summarization'),
    path(
        'summaries/trigger-single/<uuid:article_pk>/',
        trigger_single_summarization,
        name='trigger-single-summarization'),
    path(
        'summaries/search/',
        ArticleSummarySearchView.as_view(),
        name='summary-search'),
    path(
        'summaries/feedback/',
        record_summary_feedback,
        name='record-summary-feedback'),
]
