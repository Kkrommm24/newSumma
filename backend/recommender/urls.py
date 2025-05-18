from django.urls import path
from recommender.views.recommend import get_recommendations
from recommender.views.tracking import track_source_click, log_summary_view_time

urlpatterns = [
    path('recommendations/', get_recommendations, name='get-recommendations'),
    path('log-view-time/', log_summary_view_time, name='log-summary-view-time'),
    path('track-source-click/', track_source_click, name='track-source-click'),
]
