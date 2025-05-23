from news.models import User, NewsArticle, NewsSummary, NewsSource, ArticleStats, Comment, UserPreference
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

class AdminService:
    def get_system_stats(self):
        """Lấy thống kê hệ thống"""
        total_users = User.objects.count()
        total_articles = NewsArticle.objects.count()
        total_summaries = NewsSummary.objects.count()
        total_comments = ArticleStats.objects.aggregate(total=Sum('comment_count'))['total'] or 0
        total_views = ArticleStats.objects.aggregate(total=Sum('view_count'))['total'] or 0
        
        # Thống kê trong 24h gần nhất
        last_24h = timezone.now() - timedelta(days=1)
        new_users_24h = User.objects.filter(created_at__gte=last_24h).count()
        new_articles_24h = NewsArticle.objects.filter(created_at__gte=last_24h).count()
        new_summaries_24h = NewsSummary.objects.filter(created_at__gte=last_24h).count()
        
        return {
            'total_users': total_users,
            'total_articles': total_articles,
            'total_summaries': total_summaries,
            'total_comments': total_comments,
            'total_views': total_views,
            'new_users_24h': new_users_24h,
            'new_articles_24h': new_articles_24h,
            'new_summaries_24h': new_summaries_24h
        }
    
    def get_source_stats(self):
        """Lấy thống kê theo nguồn tin"""
        sources = NewsSource.objects.all()
        stats = []
        
        for source in sources:
            article_count = NewsArticle.objects.filter(source_id=source.id).count()
            summary_count = NewsSummary.objects.filter(article_id__in=NewsArticle.objects.filter(source_id=source.id).values_list('id', flat=True)).count()
            
            stats.append({
                'source_name': source.name,
                'article_count': article_count,
                'summary_count': summary_count,
                'last_scraped': source.last_scraped
            })
            
        return stats
    
    def get_all_users(self):
        """Lấy danh sách tất cả người dùng"""
        return User.objects.all().order_by('-created_at')
    
    def get_users_by_keyword(self, keyword):
        """Lấy danh sách người dùng theo từ khóa yêu thích"""
        try:
            # Lấy tất cả preferences có chứa từ khóa này
            preferences = UserPreference.objects.filter(favorite_keywords__contains=[keyword])
            
            # Lấy danh sách user_id từ preferences
            user_ids = preferences.values_list('user_id', flat=True)
            
            # Lấy thông tin người dùng
            users = User.objects.filter(id__in=user_ids).order_by('-created_at')
            
            return users
        except Exception as e:
            print(f"Error getting users by keyword: {str(e)}")
            return User.objects.none()
    
    def get_user_by_id(self, user_id):
        """Lấy thông tin người dùng theo ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def get_all_articles(self):
        """Lấy danh sách tất cả bài viết"""
        return NewsArticle.objects.all().order_by('-created_at')
    
    def get_all_summaries(self):
        """Lấy danh sách tất cả tóm tắt"""
        return NewsSummary.objects.all().order_by('-created_at')
    
    def delete_article(self, article_id):
        """Xóa bài viết"""
        try:
            article = NewsArticle.objects.get(id=article_id)
            article.delete()
            return True
        except NewsArticle.DoesNotExist:
            return False
    
    def delete_summary(self, summary_id):
        """Xóa tóm tắt"""
        try:
            summary = NewsSummary.objects.get(id=summary_id)
            summary.delete()
            return True
        except NewsSummary.DoesNotExist:
            return False
    
    def get_all_comments(self):
        """Lấy danh sách tất cả bình luận"""
        return Comment.objects.all().order_by('-created_at')
    
    def delete_comment(self, comment_id):
        """Xóa bình luận"""
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            return True
        except Comment.DoesNotExist:
            return False
    
    def get_all_favorite_words(self):
        """Lấy danh sách từ khóa yêu thích và số người dùng"""
        # Lấy tất cả các từ khóa yêu thích từ tất cả người dùng
        all_keywords = []
        for preference in UserPreference.objects.all():
            all_keywords.extend(preference.favorite_keywords)
        
        # Đếm số lần xuất hiện của mỗi từ khóa
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Chuyển đổi thành danh sách các từ khóa và số người dùng
        favorite_words = [
            {'keyword': keyword, 'user_count': count}
            for keyword, count in keyword_counts.items()
        ]
        
        return sorted(favorite_words, key=lambda x: x['user_count'], reverse=True)
    
    def delete_favorite_word(self, keyword):
        """Xóa từ khóa yêu thích khỏi tất cả người dùng"""
        try:
            # Lấy tất cả preferences có chứa từ khóa này
            preferences = UserPreference.objects.filter(favorite_keywords__contains=[keyword])
            
            # Xóa từ khóa khỏi mỗi preference
            for preference in preferences:
                preference.favorite_keywords.remove(keyword)
                preference.save()
            
            return True
        except Exception as e:
            print(f"Error deleting favorite word: {str(e)}")
            return False
