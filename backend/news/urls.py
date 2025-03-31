from django.urls import path, include
from rest_framework.routers import DefaultRouter
from news.views.crawl import CrawlerViewSet
from news.views.summary import get_summaries, ArticleSummaryViewSet

router = DefaultRouter()
router.register(r'summarizers', ArticleSummaryViewSet, basename='summarizer')
router.register(r'crawlers', CrawlerViewSet, basename='crawler')

urlpatterns = [
    path('', include(router.urls)),
    path('summaries/', get_summaries, name='get-summaries'),
]
