import random
from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import Comment, User, NewsArticle

class Command(BaseCommand):
    help = 'Seed comments into the database'

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
                num_comments = 50

                for i in range(num_comments):
                    user = random.choice(users)
                    article = random.choice(articles)
                    
                    # Chọn một mẫu ngẫu nhiên và điền thông tin (nếu có)
                    template = random.choice(comment_templates)
                    content = template.format(topic=random.choice(topics), user=user.username)
                    
                    comments_to_create.append(
                        Comment(
                            user_id=user.id,
                            article_id=article.id,
                            content=content
                        )
                    )
                    if (i + 1) % 10 == 0:
                         self.stdout.write(f"   ➕ Đã chuẩn bị {i + 1}/{num_comments} comments...")

                Comment.objects.bulk_create(comments_to_create)
                self.stdout.write(self.style.SUCCESS(f"✔ Đã tạo thành công {len(comments_to_create)} comments."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Lỗi khi seed comments: {str(e)}")) 