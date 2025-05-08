from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from news.models import Comment, NewsSummary, User

def get_comments_by_summary_id(summary_id: str):
    summary = get_object_or_404(NewsSummary, id=summary_id)
    article_id = summary.article_id
    
    comments = Comment.objects.filter(article_id=article_id).order_by('-created_at')
    
    return comments
