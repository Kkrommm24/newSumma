from django.shortcuts import get_object_or_404
from news.models import Comment, ArticleStats
from summarizer.models import NewsSummary
from django.db.models import F


def get_comments_by_summary_id(summary_id: str):
    summary = get_object_or_404(NewsSummary, id=summary_id)
    article_id = summary.article_id

    comments = Comment.objects.filter(
        article_id=article_id).order_by('-created_at')

    return comments


def update_stats_for_new_comment(article_id: str):
    if not article_id:
        return
    article_stats, created = ArticleStats.objects.get_or_create(
        article_id=article_id,
        defaults={'comment_count': 1}
    )
    if not created:
        ArticleStats.objects.filter(article_id=article_id).update(
            comment_count=F('comment_count') + 1
        )


def update_stats_for_deleted_comment(article_id: str):
    if not article_id:
        return
    ArticleStats.objects.filter(
        article_id=article_id,
        comment_count__gt=0
    ).update(
        comment_count=F('comment_count') - 1
    )
