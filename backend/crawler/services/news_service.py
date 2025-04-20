import uuid
from django.utils import timezone
from news.models import Category, NewsArticle, NewsArticleCategory, NewsSource
from django.utils.dateparse import parse_datetime
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def save_articles_with_categories(source_name, source_url, articles):
    if not articles:
        logger.info("Không có bài viết nào để lưu.")
        return 0
        
    try:
        source, _ = NewsSource.objects.get_or_create(
            website=source_url,
            defaults={"name": source_name, "last_scraped": timezone.now()}
        )
        source.last_scraped = timezone.now()
        source.save(update_fields=['last_scraped'])

        category_names = {article.get("category_name") for article in articles if article.get("category_name")}

        categories_in_db = Category.objects.filter(name__in=category_names)

        category_map = {cat.name: cat for cat in categories_in_db}
        
        missing_categories = category_names - set(category_map.keys())
        if missing_categories:
            logger.error(f"❌ Lỗi: Các category sau không tồn tại trong DB: {missing_categories}. Không thể lưu bài viết.")

            return 0
        # ------------------------------------

        articles_to_create = []
        article_category_relations_to_create = []
        valid_article_urls = set()
        
        for article in articles:
            url = article.get("url")
            if not url or url in valid_article_urls:
                logger.warning(f"⚠️ Bỏ qua bài viết bị thiếu URL hoặc URL trùng lặp trong batch: {url}")
                continue
            
            category_name = article.get("category_name")
            category_obj = category_map.get(category_name)

            if not category_obj:
                 logger.warning(f"⚠️ Bỏ qua bài viết vì không tìm thấy category '{category_name}' (đã kiểm tra trước đó?): {article.get('title')}")
                 continue

            article_id = uuid.uuid4()
            published_time = parse_datetime(article.get("published_at")) if article.get("published_at") else timezone.now()
            
            articles_to_create.append(NewsArticle(
                id=article_id,
                title=article["title"],
                content=article["content"],
                url=url,
                image_url=article.get("image_url"),
                source_id=source.id,
                published_at=published_time
            ))
            
            article_category_relations_to_create.append(NewsArticleCategory(
                article_id=article_id,
                category_id=category_obj.id
            ))
            valid_article_urls.add(url)

        saved_count = 0
        if articles_to_create:
            try:
                with transaction.atomic():
                    created_articles = NewsArticle.objects.bulk_create(articles_to_create, ignore_conflicts=True)
                    if article_category_relations_to_create:
                         NewsArticleCategory.objects.bulk_create(article_category_relations_to_create, ignore_conflicts=True)
                         
                    saved_count = len(created_articles)
                    logger.info(f"💾 Đã bulk_create {saved_count} bài viết và gán category.")

            except Exception as e:
                logger.exception(f"❌ Lỗi trong quá trình bulk_create: {e}")
                return 0

        return saved_count

    except Exception as e:
        logger.exception(f"❌ Lỗi nghiêm trọng trong save_articles_with_categories: {e}")
        return 0
