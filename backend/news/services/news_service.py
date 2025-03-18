import uuid
from django.utils import timezone
from news.models import Category, NewsArticle, NewsArticleCategory, NewsSource
from django.utils.dateparse import parse_datetime
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def save_articles_with_categories(source_name, source_url, articles):
    try:
        source, _ = NewsSource.objects.get_or_create(
            website=source_url,
            defaults={"name": source_name, "last_scraped": timezone.now()}
        )
        source.last_scraped = timezone.now()
        source.save()

        count = 0
        with transaction.atomic():
            for article in articles:
                news = NewsArticle.objects.create(
                    id=uuid.uuid4(),
                    title=article["title"],
                    content=article["content"],
                    url=article["url"],
                    image_url=article["image_url"],
                    source_id=source.id,
                    published_at=parse_datetime(article.get("published_at", timezone.now()))
                )

                # Gán category nếu có
                category_name = article.get("category_name")

                if category_name:
                    category = Category.objects.get(name=category_name)
                    NewsArticleCategory.objects.create(
                        article_id=news.id,
                        category_id=category.id
                    )
                else:
                    logger.warning("⚠️ Không có category cho bài viết")
                    news.delete()
                    continue

                count += 1

            logger.info(f"💾 Lưu {count} bài viết vào database...")

        return count
    except Exception as e:
        logger.error(f"❌ Lỗi khi lưu dữ liệu bài viết: {e}")
