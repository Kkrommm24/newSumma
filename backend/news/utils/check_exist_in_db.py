from news.models import Category, NewsArticle
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def check_url_exist(url):
    try:
        return NewsArticle.objects.filter(url=url).exists()
    except Exception as e:
        logger.error(f"❌ Lỗi khi kiểm tra URL trong database: {e}")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM news_newsarticle WHERE url = %s", [url])
                result = cursor.fetchone()[0]
                return result > 0
        except Exception as e:
            logger.error(f"❌ Lỗi nghiêm trọng khi kiểm tra URL: {e}")
            return False
        
def check_category_exist(name):
    try:
        return Category.objects.filter(name=name).exists()
    except Exception as e:
        logger.error(f"❌ Lỗi khi kiểm tra category trong database: {e}")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM news_category WHERE name = %s", [name])
                result = cursor.fetchone()[0]
                return result > 0
        except Exception as e:
            logger.error(f"❌ Lỗi nghiêm trọng khi kiểm tra category: {e}")
            return False
