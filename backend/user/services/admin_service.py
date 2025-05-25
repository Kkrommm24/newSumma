from news.models import User, NewsArticle, NewsSummary, NewsSource, ArticleStats, Comment, UserPreference
from django.db.models import Sum
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
    
    def get_all_users(self, filters=None, ordering=None):
        """Lấy danh sách tất cả người dùng"""
        queryset = User.objects.all()
        
        if filters:
            if 'username' in filters:
                queryset = queryset.filter(username__in=filters['username'])
            if 'email' in filters:
                queryset = queryset.filter(email__in=filters['email'])
            if 'is_active' in filters:
                queryset = queryset.filter(is_active__in=filters['is_active'])
        
        # Áp dụng sắp xếp nếu có
        if ordering:
            # Kiểm tra xem trường sắp xếp có hợp lệ không
            valid_fields = ['username', 'email', 'is_active', 'created_at', 'updated_at']
            field = ordering.lstrip('-')
            if field in valid_fields:
                queryset = queryset.order_by(ordering)
            else:
                # Nếu trường không hợp lệ, sắp xếp mặc định theo created_at
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
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
    
    def get_all_articles(self, filters=None, ordering=None):
        """Lấy danh sách tất cả bài viết"""
        queryset = NewsArticle.objects.all()
        
        if filters:
            if 'title' in filters:
                queryset = queryset.filter(title__in=filters['title'])
            if 'source_name' in filters:
                source_ids = NewsSource.objects.filter(name__in=filters['source_name']).values_list('id', flat=True)
                queryset = queryset.filter(source_id__in=source_ids)
        
        # Áp dụng sắp xếp nếu có
        if ordering:
            valid_fields = ['title', 'source_id', 'published_at', 'created_at', 'updated_at']
            field = ordering.lstrip('-')
            if field == 'source_name':
                # Xử lý sắp xếp theo tên nguồn
                source_ids = NewsSource.objects.values_list('id', 'name')
                source_dict = dict(source_ids)
                queryset = list(queryset)
                reverse = ordering.startswith('-')
                queryset.sort(key=lambda x: source_dict.get(x.source_id, ''), reverse=reverse)
            elif field in valid_fields:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_all_summaries(self, filters=None, ordering=None):
        """Lấy danh sách tất cả tóm tắt"""
        queryset = NewsSummary.objects.all()
        
        if filters:
            if 'article_title' in filters:
                article_ids = NewsArticle.objects.filter(title__in=filters['article_title']).values_list('id', flat=True)
                queryset = queryset.filter(article_id__in=article_ids)
        
        # Áp dụng sắp xếp nếu có
        if ordering:
            valid_fields = ['upvotes', 'downvotes', 'created_at', 'updated_at']
            field = ordering.lstrip('-')
            if field == 'article_title':
                # Xử lý sắp xếp theo tiêu đề bài viết
                article_ids = NewsArticle.objects.values_list('id', 'title')
                article_dict = dict(article_ids)
                queryset = list(queryset)
                reverse = ordering.startswith('-')
                queryset.sort(key=lambda x: article_dict.get(x.article_id, ''), reverse=reverse)
            elif field in valid_fields:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
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
    
    def get_all_comments(self, filters=None, ordering=None):
        """Lấy danh sách tất cả bình luận"""
        queryset = Comment.objects.all()
        
        if filters:
            if 'username' in filters:
                user_ids = User.objects.filter(username__in=filters['username']).values_list('id', flat=True)
                queryset = queryset.filter(user_id__in=user_ids)
            if 'article_title' in filters:
                article_ids = NewsArticle.objects.filter(title__in=filters['article_title']).values_list('id', flat=True)
                queryset = queryset.filter(article_id__in=article_ids)
        
        # Áp dụng sắp xếp nếu có
        if ordering:
            valid_fields = ['created_at', 'updated_at']
            field = ordering.lstrip('-')
            if field == 'username':
                # Xử lý sắp xếp theo username
                user_ids = User.objects.values_list('id', 'username')
                user_dict = dict(user_ids)
                queryset = list(queryset)
                reverse = ordering.startswith('-')
                queryset.sort(key=lambda x: user_dict.get(x.user_id, ''), reverse=reverse)
            elif field == 'article_title':
                # Xử lý sắp xếp theo tiêu đề bài viết
                article_ids = NewsArticle.objects.values_list('id', 'title')
                article_dict = dict(article_ids)
                queryset = list(queryset)
                reverse = ordering.startswith('-')
                queryset.sort(key=lambda x: article_dict.get(x.article_id, ''), reverse=reverse)
            elif field in valid_fields:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def delete_comment(self, comment_id):
        """Xóa bình luận"""
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            return True
        except Comment.DoesNotExist:
            return False
    
    def get_all_favorite_words(self, filters=None, ordering=None):
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
        
        # Áp dụng sắp xếp nếu có
        if ordering:
            field = ordering.lstrip('-')
            reverse = ordering.startswith('-')
            
            if field == 'keyword':
                favorite_words.sort(key=lambda x: x['keyword'], reverse=reverse)
            elif field == 'user_count':
                favorite_words.sort(key=lambda x: x['user_count'], reverse=reverse)
            else:
                # Mặc định sắp xếp theo số người dùng giảm dần
                favorite_words.sort(key=lambda x: x['user_count'], reverse=True)
        else:
            # Mặc định sắp xếp theo số người dùng giảm dần
            favorite_words.sort(key=lambda x: x['user_count'], reverse=True)
        
        return favorite_words
    
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
