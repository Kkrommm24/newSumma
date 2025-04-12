from django.urls import path
from recommender.views.recommend import get_recommended_articles

urlpatterns = [
    # URL for recommendations
    path('recommendations/', get_recommended_articles, name='get-recommendations'),
]
