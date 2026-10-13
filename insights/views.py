
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from posts.models import Post, Reel, Follow, Comment
from insights.models import ContentView


@login_required
def insights_dashboard(request):
    user = request.user

    # Reporting period: 7, 30, or 90 days
    period = request.GET.get("period", "7")
    if period not in ("7", "30", "90"):
        period = "7"

    since = timezone.now() - timedelta(days=int(period))

    # User's own content
    own_posts = Post.objects.filter(user=user, video__isnull=True)
    own_reels = Reel.objects.filter(user=user)

    post_type = ContentType.objects.get_for_model(Post)
    reel_type = ContentType.objects.get_for_model(Reel)

    post_ids = own_posts.values_list("id", flat=True)
    reel_ids = own_reels.values_list("id", flat=True)

    # Views recorded during the selected reporting period
    post_views_qs = ContentView.objects.filter(
        content_type=post_type,
        object_id__in=post_ids,
        viewed_at__gte=since,
    )

    reel_views_qs = ContentView.objects.filter(
        content_type=reel_type,
        object_id__in=reel_ids,
        viewed_at__gte=since,
    )

    total_post_views = post_views_qs.count()
    total_reel_views = reel_views_qs.count()
    total_views = total_post_views + total_reel_views

    # Likes and comments received on the user's content
    total_post_likes = sum(post.likes.count() for post in own_posts)
    total_reel_likes = sum(reel.likes.count() for reel in own_reels)
    total_likes = total_post_likes + total_reel_likes

    total_comments = Comment.objects.filter(
        post__in=own_posts
    ).count()

    # Count reel comments if your ReelComment model exists
    try:
        from posts.models import ReelComment

        total_comments += ReelComment.objects.filter(
            reel__in=own_reels
        ).count()
    except ImportError:
        pass

    # Published content
    total_posts = own_posts.count()
    total_reels = own_reels.count()

    # Followers
    followers = Follow.objects.filter(following=user).count()

    # Estimated reach: distinct recorded viewer/session identifiers.
    # Anonymous views without a session key may not be identifiable.
    post_reach = post_views_qs.exclude(
        session_key=""
    ).values("viewer_id", "session_key").distinct().count()

    reel_reach = reel_views_qs.exclude(
        session_key=""
    ).values("viewer_id", "session_key").distinct().count()

    total_reach = post_reach + reel_reach

    # Engagement rate based on likes + comments divided by views
    engagement_rate = (
        round(((total_likes + total_comments) / total_views) * 100, 2)
        if total_views else 0
    )

    # Top posts and reels for the selected period
    top_posts = []
    for post in own_posts:
        views = post_views_qs.filter(object_id=post.id).count()
        if views:
            top_posts.append({"object": post, "views": views})

    top_posts.sort(key=lambda item: item["views"], reverse=True)

    top_reels = []
    for reel in own_reels:
        views = reel_views_qs.filter(object_id=reel.id).count()
        if views:
            top_reels.append({"object": reel, "views": views})

    top_reels.sort(key=lambda item: item["views"], reverse=True)

    context = {
        "period": period,
        "total_views": total_views,
        "total_reach": total_reach,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_post_views": total_post_views,
        "total_reel_views": total_reel_views,
        "engagement_rate": engagement_rate,
        "total_posts": total_posts,
        "total_reels": total_reels,
        "followers": followers,
        "top_posts": top_posts[:5],
        "top_reels": top_reels[:5],

        # Keep the existing home-insights variable names available
        "insights_post_views": total_post_views,
        "insights_reel_views": total_reel_views,
        "insights_total_views": total_views,
        "insights_total_likes": total_likes,
        "insights_followers": followers,
    }

    return render(request, "insights/dashboard.html", context)
