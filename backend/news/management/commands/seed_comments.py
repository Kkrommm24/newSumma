import random
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from news.models import Comment, User, NewsArticle, ArticleStats
from django.db.models import Count

class Command(BaseCommand):
    help = 'Seed comments into the database and update ArticleStats'

    def handle(self, *args, **options):
        # Danh sách các mẫu comment đơn giản
        comment_templates = [
            "Bài viết rất hay! Cảm ơn tác giả.",
            "Tôi đồng ý với quan điểm này.",
            "Thông tin rất hữu ích.",
            "Có ai có ý kiến khác không?",
            "Tin tức này thật bất ngờ.",
            "Tôi nghĩ cần xem xét thêm về {topic}.",
            "Cảm ơn {user} đã chia sẻ.",
            "Chủ đề này đang rất nóng.",
            "Tuyệt vời!",
            "Bài phân tích sâu sắc.",
        ]
        topics = ["vấn đề này", "tin tức này", "chủ đề này", "điểm này"]

        try:
            with transaction.atomic():
                self.stdout.write("🗑️  Đang xóa tất cả Comment cũ...")
                Comment.objects.all().delete()
                self.stdout.write("🔄  Đang reset comment_count trong ArticleStats về 0 cho các bài viết có comment...")

                users = list(User.objects.all()[:10])
                articles = list(NewsArticle.objects.all()[:20])

                if not users:
                    self.stdout.write(self.style.WARNING("⚠️ Không tìm thấy User nào. Bỏ qua seed comments."))
                    return
                
                if not articles:
                    self.stdout.write(self.style.WARNING("⚠️ Không tìm thấy NewsArticle nào. Bỏ qua seed comments."))
                    return

                self.stdout.write(self.style.NOTICE(f"⏳ Seeding comments cho {len(articles)} bài viết và {len(users)} người dùng..."))
                
                comments_to_create = []
                num_comments_to_seed = 50
                article_comment_counts = {article.id: 0 for article in articles}

                for i in range(num_comments_to_seed):
                    user = random.choice(users)
                    article = random.choice(articles)
                    
                    template = random.choice(comment_templates)
                    content = template.format(topic=random.choice(topics), user=user.username)
                    
                    comments_to_create.append(
                        Comment(
                            user_id=user.id,
                            article_id=article.id,
                            content=content
                        )
                    )
                    article_comment_counts[article.id] += 1

                    if (i + 1) % 10 == 0:
                         self.stdout.write(f"   ➕ Đã chuẩn bị {i + 1}/{num_comments_to_seed} comments...")

                Comment.objects.bulk_create(comments_to_create)
                self.stdout.write(self.style.SUCCESS(f"✔ Đã tạo thành công {len(comments_to_create)} comments."))

                self.stdout.write("🔄  Đang cập nhật comment_count trong ArticleStats...")
                articles_updated_stats = 0
                for article_id, count in article_comment_counts.items():
                    if count > 0:
                        ArticleStats.objects.update_or_create(
                            article_id=article_id,
                            defaults={'comment_count': count}
                        )
                        articles_updated_stats += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Đã cập nhật comment_count cho {articles_updated_stats} bài viết trong ArticleStats."))

        except IntegrityError as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi IntegrityError khi seed comments (có thể do article_id hoặc user_id không hợp lệ): {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi khác khi seed comments: {str(e)}")) 