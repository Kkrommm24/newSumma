from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from news.crawlers.baomoi.tasks import crawl_baomoi_articles
from news.crawlers.vnexpress.tasks import crawl_vnexpress_articles


@api_view(['POST'])
def crawl_baomoi_view(request):
    try:
        count = crawl_baomoi_articles()
        return Response({"message": f"Crawled {count} articles"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def crawl_vnexpress_view(request):
    try:
        count = crawl_vnexpress_articles()
        return Response({"message": f"Crawled {count} articles"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
