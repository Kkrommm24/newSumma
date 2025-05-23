from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from user.services.admin_service import AdminService
from user.serializers.admin_serializers import (
    AdminUserSerializer, AdminArticleSerializer, 
    AdminSummarySerializer, AdminStatsSerializer,
    AdminCommentSerializer, AdminFavoriteWordSerializer
)
from crawler.crawlers.baomoi.tasks import crawl_baomoi_articles
from crawler.crawlers.vnexpress.tasks import crawl_vnexpress_articles
from summarizer.summarizers.llama.tasks import generate_article_summaries

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number
        })

class AdminBaseView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_service = AdminService()
        self.paginator = self.pagination_class()

    def paginate_queryset(self, queryset):
        return self.paginator.paginate_queryset(queryset, self.request)

class AdminDashboardView(AdminBaseView):
    def get(self, request):
        """Lấy thống kê hệ thống"""
        stats = self.admin_service.get_system_stats()
        source_stats = self.admin_service.get_source_stats()
        
        return Response({
            'system_stats': stats,
            'source_stats': source_stats
        })

class AdminCrawlView(AdminBaseView):
    def post(self, request):
        """Kích hoạt crawl dữ liệu từ các nguồn"""
        source = request.data.get('source')
        if not source:
            return Response({'error': 'Vui lòng chọn nguồn tin'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            if source == 'baomoi':
                crawl_baomoi_articles.delay()
            elif source == 'vnexpress':
                crawl_vnexpress_articles.delay()
            else:
                return Response({'error': 'Nguồn tin không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({'message': f'Đã bắt đầu crawl từ {source}'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminSummarizeView(AdminBaseView):
    def post(self, request):
        """Kích hoạt tạo tóm tắt cho các bài viết"""
        try:
            generate_article_summaries.delay()
            return Response({'message': 'Đã bắt đầu tạo tóm tắt cho các bài viết'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminUserManagementView(AdminBaseView):
    def get(self, request):
        """Lấy danh sách người dùng"""
        users = self.admin_service.get_all_users()
        page = self.paginate_queryset(users)
        serializer = AdminUserSerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Tạo người dùng mới"""
        serializer = AdminUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, user_id):
        """Khóa/Mở khóa tài khoản người dùng"""
        try:
            user = self.admin_service.get_user_by_id(user_id)
            if not user:
                return Response({'error': 'Không tìm thấy người dùng'}, status=status.HTTP_404_NOT_FOUND)
            
            # Không cho phép khóa tài khoản admin
            if user.is_staff:
                return Response({'error': 'Không thể khóa tài khoản admin'}, status=status.HTTP_400_BAD_REQUEST)
            
            is_active = request.data.get('is_active')
            if is_active is None:
                return Response({'error': 'Thiếu trường is_active'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_active = is_active
            user.save()
            
            return Response(AdminUserSerializer(user).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminArticleManagementView(AdminBaseView):
    def get(self, request):
        """Lấy danh sách bài viết"""
        articles = self.admin_service.get_all_articles()
        page = self.paginate_queryset(articles)
        serializer = AdminArticleSerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    def delete(self, request, article_id):
        """Xóa bài viết"""
        try:
            self.admin_service.delete_article(article_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminSummaryManagementView(AdminBaseView):
    def get(self, request):
        """Lấy danh sách tóm tắt"""
        summaries = self.admin_service.get_all_summaries()
        page = self.paginate_queryset(summaries)
        serializer = AdminSummarySerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    def delete(self, request, summary_id):
        """Xóa tóm tắt"""
        try:
            self.admin_service.delete_summary(summary_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminCommentManagementView(AdminBaseView):
    def get(self, request):
        """Lấy danh sách bình luận"""
        comments = self.admin_service.get_all_comments()
        page = self.paginate_queryset(comments)
        serializer = AdminCommentSerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    def delete(self, request, comment_id):
        """Xóa bình luận"""
        try:
            self.admin_service.delete_comment(comment_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminFavoriteWordManagementView(AdminBaseView):
    def get(self, request):
        """Lấy danh sách từ khóa yêu thích"""
        keyword = request.query_params.get('keyword')
        if keyword:
            # Nếu có keyword, trả về danh sách user có từ khóa đó
            users = self.admin_service.get_users_by_keyword(keyword)
            page = self.paginate_queryset(users)
            serializer = AdminUserSerializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)
        else:
            # Nếu không có keyword, trả về danh sách từ khóa
            favorite_words = self.admin_service.get_all_favorite_words()
            page = self.paginate_queryset(favorite_words)
            serializer = AdminFavoriteWordSerializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)

    def delete(self, request, keyword):
        """Xóa từ khóa yêu thích"""
        try:
            self.admin_service.delete_favorite_word(keyword)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
