from django.urls import path
from .views.summary import SummaryDetailView, ArticleSummaryView

urlpatterns = [
    path('summaries/<uuid:id>/', SummaryDetailView.as_view(), name='summary-detail'),
    path('articles/<uuid:article_id>/summary/', ArticleSummaryView.as_view(), name='article-summary'),
]