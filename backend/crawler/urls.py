from django.urls import path
from crawler.views.crawl import trigger_crawl_baomoi, trigger_crawl_vnexpress

urlpatterns = [
    path(
        'crawlers/trigger-baomoi/',
        trigger_crawl_baomoi,
        name='trigger-crawl-baomoi'),
    path(
        'crawlers/trigger-vnexpress/',
        trigger_crawl_vnexpress,
        name='trigger-crawl-vnexpress'),
]
