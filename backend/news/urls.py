from django.urls import path
from news.views.article import ArticleListView
from news.views.crawl import crawl_baomoi_view, crawl_vnexpress_view

urlpatterns = [
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('crawl/baomoi/', crawl_baomoi_view, name='crawl-baomoi'),
    path('crawl/vnexpress/', crawl_vnexpress_view, name='crawl-vnexpress'),
]
