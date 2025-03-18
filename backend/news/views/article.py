from rest_framework.generics import ListAPIView
from news.models import NewsArticle
from news.serializers.serializers import ArticleListSerializer

class ArticleListView(ListAPIView):
    serializer_class = ArticleListSerializer

    def get_queryset(self):
        return NewsArticle.objects.all().order_by('-published_at')
