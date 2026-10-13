
# =========================================================
# INSTALITE — CLEANED posts/views.py
# =========================================================

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import (
    Q, Count, OuterRef, Subquery, IntegerField, Value
)
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Account
from insights.models import ContentView
from insights.utils import track_content_view

from .models import (
    Post, PostImage, Like, Comment, Follow, FollowRequest,
    Notification, SavedPost, Story, StoryLike, StoryComment,
    StoryView, DirectMessage, Reel, ReelLike, ReelComment,
    SavedReel,
)


# =========================================================
# SHARED HELPERS
# =========================================================

def get_feed_context(request, posts):
    """Context shared by the home feed and post activity pages."""

    liked_posts = []
    following_ids = []
    saved_post_ids = []

    if request.user.is_authenticated:
        liked_posts = list(
            Like.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
        )

        following_ids = list(
            Follow.objects.filter(follower=request.user)
            .values_list("following_id", flat=True)
        )

        saved_post_ids = list(
            SavedPost.objects.filter(user=request.user)
            .values_list("post_id", flat=True)
        )

    return {
        "posts": posts,
        "liked_posts": liked_posts,
        "following_ids": following_ids,
        "saved_post_ids": saved_post_ids,
    }


def add_view_counts(queryset, model):
    """Annotate posts or reels with their ContentView count."""

    content_type = ContentType.objects.get_for_model(model)

    view_counts = (
        ContentView.objects
        .filter(
            content_type=content_type,
            object_id=OuterRef("pk"),
        )
        .values("object_id")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    return queryset.annotate(
        insights_views=Coalesce(
            Subquery(
                view_counts,
                output_field=IntegerField(),
            ),
            Value(0),
        )
    )


def get_suggested_users(user, limit=None):
    """
    Randomly suggest accounts the current user does not follow,
    has not already requested to follow, and does not own.
    """

    if not user.is_authenticated:
        return Account.objects.none()

    following_ids = Follow.objects.filter(
        follower=user
    ).values_list("following_id", flat=True)

    pending_request_ids = FollowRequest.objects.filter(
        sender=user,
        status=FollowRequest.PENDING,
    ).values_list("receiver_id", flat=True)

    suggestions = (
        Account.objects
        .exclude(pk=user.pk)
        .exclude(pk__in=following_ids)
        .exclude(pk__in=pending_request_ids)
        .order_by("?")
    )

    if limit is not None:
        suggestions = suggestions[:limit]

    return suggestions



def is_mutual_follow(user_a, user_b):
    """Check whether two accounts follow each other."""

    if not user_a.is_authenticated:
        return False

    if user_a == user_b:
        return True

    return (
        Follow.objects.filter(
            follower=user_a,
            following=user_b,
        ).exists()
        and Follow.objects.filter(
            follower=user_b,
            following=user_a,
        ).exists()
    )


def can_view_account(viewer, profile_user):
    """Allow public profiles; restrict private profiles to mutual follows."""

    if viewer.is_authenticated and viewer == profile_user:
        return True

    if not profile_user.private_account:
        return True

    return is_mutual_follow(viewer, profile_user)


def can_message_account(sender, receiver):
    """Require mutual follows when either account is private."""

    if sender == receiver:
        return False

    if not (sender.private_account or receiver.private_account):
        return True

    return is_mutual_follow(sender, receiver)


# =========================================================
# HOME FEED
# =========================================================

@login_required
def feed(request):
    posts = (
        Post.objects
        .filter(video__isnull=True)
        .select_related("user")
        .prefetch_related(
            "likes",
            "comments",
            "comments__user",
            "images",
        )
        .order_by("-created_at")
    )

    feed_reels = (
        Reel.objects
        .select_related("user")
        .prefetch_related(
            "likes",
            "comments",
            "comments__user",
        )
        .order_by("-created_at")
    )

    posts = add_view_counts(posts, Post)
    feed_reels = add_view_counts(feed_reels, Reel)

    context = get_feed_context(request, posts)

    context.update({
        "feed_reels": feed_reels,
        "liked_reel_ids": set(
            ReelLike.objects.filter(user=request.user)
            .values_list("reel_id", flat=True)
        ),
        "saved_reel_ids": set(
            SavedReel.objects.filter(user=request.user)
            .values_list("reel_id", flat=True)
        ),

        # Display suggestions directly on the home feed.
        "sidebar_suggested_users": get_suggested_users(
            request.user, limit=5
        ),
        "suggested_users": get_suggested_users(
            request.user, limit=5
        ),
    })

    return render(request, "posts/feed_page.html", context)


# =========================================================
# PEOPLE YOU MAY KNOW — SEE ALL
# =========================================================

@login_required
def people_you_may_know(request):
    suggestions = get_suggested_users(request.user)

    return render(
        request,
        "posts/people_you_may_know.html",
        {
            "suggested_users": suggestions,
            "sidebar_suggested_users": get_suggested_users(
                request.user, limit=5
            ),
        },
    )


# =========================================================
# CREATE POST
# =========================================================

@login_required
def create_post(request):
    if request.method == "POST":
        images = request.FILES.getlist("images")
        caption = request.POST.get("caption", "").strip()

        if not images:
            messages.error(request, "Please select at least one image.")
            return redirect("create_post")

        post = Post.objects.create(
            user=request.user,
            image=images[0],
            caption=caption,
        )

        for image in images[1:]:
            PostImage.objects.create(post=post, image=image)

        messages.success(
            request,
            "Your post has been published successfully!",
        )
        return redirect("index")

    return render(request, "posts/create_post.html")


# =========================================================
# LIKE POST
# =========================================================

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    like = Like.objects.filter(
        user=request.user, post=post
    ).first()

    if like:
        like.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

        if post.user != request.user:
            Notification.objects.create(
                actor=request.user,
                recipient=post.user,
                post=post,
                notification_type="like",
            )

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes_count": post.likes.count(),
        "post_id": post.pk,
    })


# =========================================================
# COMMENT ON POST
# =========================================================

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    text = request.POST.get("text", "").strip()

    if not text:
        messages.error(request, "Comment cannot be empty.")
        return redirect(request.META.get("HTTP_REFERER", "index"))

    comment = Comment.objects.create(
        user=request.user,
        post=post,
        text=text,
    )

    if post.user != request.user:
        Notification.objects.create(
            actor=request.user,
            recipient=post.user,
            post=post,
            comment=comment,
            notification_type="comment",
        )

    return redirect(request.META.get("HTTP_REFERER", "index"))


# =========================================================
# FOLLOW / UNFOLLOW USER
# =========================================================

@login_required
@require_POST
def follow_user(request, user_id):
    target = get_object_or_404(Account, pk=user_id)

    if target == request.user:
        return JsonResponse({
            "success": False,
            "message": "You cannot follow yourself.",
        }, status=400)

    existing_follow = Follow.objects.filter(
        follower=request.user,
        following=target,
    ).first()

    if existing_follow:
        existing_follow.delete()

        return JsonResponse({
            "success": True,
            "following": False,
            "status": "not_following",
        })

    if not target.private_account:
        Follow.objects.get_or_create(
            follower=request.user,
            following=target,
        )

        FollowRequest.objects.filter(
            sender=request.user,
            receiver=target,
            status=FollowRequest.PENDING,
        ).delete()

        Notification.objects.get_or_create(
            actor=request.user,
            recipient=target,
            notification_type="follow",
            post=None,
            comment=None,
            defaults={"is_read": False},
        )

        return JsonResponse({
            "success": True,
            "following": True,
            "status": "following",
            "followers_count": Follow.objects.filter(
                following=target
            ).count(),
        })

    follow_request = FollowRequest.objects.filter(
        sender=request.user,
        receiver=target,
    ).first()

    if follow_request:
        if follow_request.status == FollowRequest.PENDING:
            follow_request.delete()

            return JsonResponse({
                "success": True,
                "following": False,
                "status": "not_following",
                "message": "Follow request cancelled.",
            })

        follow_request.status = FollowRequest.PENDING
        follow_request.save(update_fields=["status"])
    else:
        FollowRequest.objects.create(
            sender=request.user,
            receiver=target,
            status=FollowRequest.PENDING,
        )

    return JsonResponse({
        "success": True,
        "following": False,
        "status": "requested",
        "message": "Follow request sent.",
    })


# =========================================================
# SAVE / UNSAVE POST
# =========================================================

@login_required
@require_POST
def save_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    saved_item = SavedPost.objects.filter(
        user=request.user,
        post=post,
    ).first()

    if saved_item:
        saved_item.delete()
        saved = False
    else:
        SavedPost.objects.create(user=request.user, post=post)
        saved = True

    return JsonResponse({
        "success": True,
        "saved": saved,
        "post_id": post.pk,
    })


# =========================================================
# NOTIFICATIONS
# =========================================================

@login_required
def notifications(request):
    notification_list = list(
        Notification.objects
        .filter(recipient=request.user)
        .select_related("actor", "post", "comment")
        .order_by("-created_at")
    )

    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    return render(
        request,
        "posts/notifications.html",
        {"notifications": notification_list},
    )


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    return JsonResponse({"success": True})


# =========================================================
# SAVED POSTS AND REELS
# =========================================================

@login_required
def saved_posts(request):
    saved_items = (
        SavedPost.objects
        .filter(user=request.user)
        .select_related("post", "post__user")
        .prefetch_related(
            "post__likes",
            "post__comments",
            "post__comments__user",
            "post__images",
        )
        .order_by("-created_at")
    )

    posts = [item.post for item in saved_items]

    saved_reels = (
        SavedReel.objects
        .filter(user=request.user)
        .select_related("reel", "reel__user")
        .prefetch_related(
            "reel__likes",
            "reel__comments",
            "reel__comments__user",
        )
        .order_by("-created_at")
    )

    context = get_feed_context(request, posts)
    context.update({
        "page_title": "Saved",
        "saved_reels": saved_reels,
        "saved_reel_ids": list(
            saved_reels.values_list("reel_id", flat=True)
        ),
        "liked_reel_ids": set(
            ReelLike.objects.filter(user=request.user)
            .values_list("reel_id", flat=True)
        ),
    })

    return render(request, "posts/activity.html", context)


# =========================================================
# LIKED POSTS
# =========================================================

@login_required
def liked_posts(request):
    like_items = (
        Like.objects
        .filter(user=request.user)
        .select_related("post", "post__user")
        .prefetch_related(
            "post__likes",
            "post__comments",
            "post__comments__user",
        )
        .order_by("-created_at")
    )

    posts = [item.post for item in like_items]
    context = get_feed_context(request, posts)
    context["page_title"] = "Like Activity"

    return render(request, "posts/activity.html", context)


# =========================================================
# DELETE POST
# =========================================================

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.user != request.user:
        return JsonResponse({
            "success": False,
            "message": "You cannot delete this post.",
        }, status=403)

    post.delete()

    return JsonResponse({
        "success": True,
        "message": "Post deleted successfully.",
    })


# =========================================================
# STORIES
# =========================================================

@login_required
def create_story(request):
    if request.method != "POST":
        return render(request, "create_story.html")

    files = request.FILES.getlist("files")

    if not files:
        return JsonResponse({
            "success": False,
            "message": "Please select a file.",
        }, status=400)

    created = 0

    for file in files:
        content_type = getattr(file, "content_type", "") or ""

        if content_type.startswith("image/"):
            Story.objects.create(user=request.user, image=file)
            created += 1
        elif content_type.startswith("video/"):
            Story.objects.create(user=request.user, video=file)
            created += 1

    if not created:
        return JsonResponse({
            "success": False,
            "message": "Please select a valid image or video.",
        }, status=400)

    return JsonResponse({"success": True, "created": created})


@login_required
def stories(request):
    Story.objects.filter(expires_at__lte=timezone.now()).delete()

    active_stories = (
        Story.objects
        .filter(expires_at__gt=timezone.now())
        .select_related("user")
        .order_by("-created_at")
    )

    return render(request, "posts/story.html", {
        "stories": active_stories,
        "my_stories": active_stories.filter(user=request.user),
        "other_stories": active_stories.exclude(user=request.user),
    })


@login_required
@require_POST
def delete_story(request, story_id):
    story = get_object_or_404(Story, pk=story_id)

    if story.user != request.user:
        return JsonResponse({
            "success": False,
            "message": "You cannot delete this story.",
        }, status=403)

    story.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def like_story(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        expires_at__gt=timezone.now(),
    )

    like = StoryLike.objects.filter(
        story=story, user=request.user
    ).first()

    if like:
        like.delete()
        liked = False
    else:
        StoryLike.objects.create(story=story, user=request.user)
        liked = True

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes_count": StoryLike.objects.filter(story=story).count(),
    })


@login_required
@require_POST
def view_story(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        expires_at__gt=timezone.now(),
    )

    StoryView.objects.update_or_create(
        story=story,
        user=request.user,
        defaults={"viewed_at": timezone.now()},
    )

    return JsonResponse({"success": True})


@login_required
def story_interaction_data(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        expires_at__gt=timezone.now(),
    )

    return JsonResponse({
        "success": True,
        "liked": StoryLike.objects.filter(
            story=story, user=request.user
        ).exists(),
        "likes_count": StoryLike.objects.filter(story=story).count(),
        "comments_count": StoryComment.objects.filter(story=story).count(),
    })


@login_required
@require_POST
def comment_story(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        expires_at__gt=timezone.now(),
    )

    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({
            "success": False,
            "message": "Comment cannot be empty.",
        }, status=400)

    StoryComment.objects.create(
        story=story,
        user=request.user,
        text=text,
    )

    return JsonResponse({
        "success": True,
        "comments_count": StoryComment.objects.filter(
            story=story
        ).count(),
    })


@login_required
@require_POST
def share_story(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        expires_at__gt=timezone.now(),
    )

    receiver_id = request.POST.get("receiver_id")
    receiver = get_object_or_404(Account, pk=receiver_id)

    if receiver == request.user:
        return JsonResponse({
            "success": False,
            "message": "You cannot share a story with yourself.",
        }, status=400)

    if not can_message_account(request.user, receiver):
        return JsonResponse({
            "success": False,
            "message": "You cannot message this account.",
        }, status=403)

    story_url = request.build_absolute_uri(f"/stories/?story={story.pk}")

    DirectMessage.objects.create(
        sender=request.user,
        receiver=receiver,
        text=f"📸 {request.user.username} shared a story with you.\n{story_url}",
    )

    return JsonResponse({
        "success": True,
        "message": f"Story shared with {receiver.username}.",
    })


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):
    user = request.user

    posts = Post.objects.filter(
        user=user, video__isnull=True
    ).order_by("-created_at")

    reels = Reel.objects.filter(
        user=user
    ).order_by("-created_at")

    context = {
        "profile_user": user,
        "posts": posts,
        "reels": reels,
        "posts_count": posts.count(),
        "followers_count": Follow.objects.filter(following=user).count(),
        "following_count": Follow.objects.filter(follower=user).count(),
    }

    return render(request, "profile.html", context)


@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        bio = request.POST.get("bio", "").strip()
        profile_picture = request.FILES.get("profile_picture")

        if not username:
            messages.error(request, "Username cannot be empty.")
            return redirect("edit_profile")

        if Account.objects.filter(
            username=username
        ).exclude(pk=user.pk).exists():
            messages.error(request, "This username is already taken.")
            return render(
                request,
                "posts/edit_profile.html",
                {"profile_user": user},
            )

        user.username = username
        user.full_name = full_name
        user.bio = bio

        if profile_picture:
            user.profile_picture = profile_picture

        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(
        request,
        "posts/edit_profile.html",
        {"profile_user": user},
    )


@login_required
def public_profile(request, user_id):
    profile_user = get_object_or_404(Account, pk=user_id)

    is_following = Follow.objects.filter(
        follower=request.user,
        following=profile_user,
    ).exists()

    follows_viewer = Follow.objects.filter(
        follower=profile_user,
        following=request.user,
    ).exists()

    follow_request_pending = FollowRequest.objects.filter(
        sender=request.user,
        receiver=profile_user,
        status=FollowRequest.PENDING,
    ).exists()

    can_view = can_view_account(request.user, profile_user)

    if can_view:
        user_posts = (
            Post.objects
            .filter(user=profile_user, video__isnull=True)
            .select_related("user")
            .prefetch_related("likes", "comments", "comments__user", "images")
            .order_by("-created_at")
        )

        user_reels = Reel.objects.filter(
            user=profile_user
        ).order_by("-created_at")
    else:
        user_posts = Post.objects.none()
        user_reels = Reel.objects.none()

    return render(request, "posts/public_profile.html", {
        "profile_user": profile_user,
        "user_posts": user_posts,
        "reels": user_reels,
        "is_following": is_following,
        "follows_viewer": follows_viewer,
        "follow_request_pending": follow_request_pending,
        "can_view": can_view,
        "followers_count": Follow.objects.filter(
            following=profile_user
        ).count(),
        "following_count": Follow.objects.filter(
            follower=profile_user
        ).count(),
        "posts_count": user_posts.count(),
    })


# =========================================================
# USER SEARCH
# =========================================================

def search_users(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"users": []})

    users = Account.objects.filter(
        Q(username__icontains=query)
        | Q(full_name__icontains=query)
    )

    if request.user.is_authenticated:
        users = users.exclude(pk=request.user.pk)

    users = users.order_by("username")[:10]

    results = []

    for user in users:
        picture = user.profile_picture.url if user.profile_picture else ""

        results.append({
            "id": user.pk,
            "name": user.full_name.strip() if user.full_name else user.username,
            "username": user.username,
            "profile_picture": picture,
            "profile_url": f"/posts/profile/{user.pk}/",
        })

    return JsonResponse({"users": results})


# =========================================================
# EXPLORE
# =========================================================

def explore(request):
    search = request.GET.get("q", "").strip()

    posts = (
        Post.objects
        .select_related("user")
        .prefetch_related("likes", "comments")
        .order_by("-created_at")
    )

    reels = (
        Reel.objects
        .select_related("user")
        .prefetch_related("likes", "comments")
        .order_by("-created_at")
    )

    users = Account.objects.none()

    if search:
        users = Account.objects.filter(
            Q(username__icontains=search)
            | Q(full_name__icontains=search)
        )

        if request.user.is_authenticated:
            users = users.exclude(pk=request.user.pk)

        users = users.order_by("username")[:10]

        posts = posts.filter(
            Q(caption__icontains=search)
            | Q(user__username__icontains=search)
        )

        reels = reels.filter(
            Q(caption__icontains=search)
            | Q(user__username__icontains=search)
        )

    return render(request, "posts/explore.html", {
        "posts": posts,
        "reels": reels,
        "users": users,
        "search": search,
    })


# =========================================================
# MESSAGES
# =========================================================

@login_required
def messages_inbox(request):
    current_user = request.user

    all_messages = (
        DirectMessage.objects
        .filter(
            Q(sender=current_user) | Q(receiver=current_user)
        )
        .select_related("sender", "receiver")
        .order_by("-created_at")
    )

    conversations = []
    added_users = set()

    for message in all_messages:
        other_user = (
            message.receiver
            if message.sender == current_user
            else message.sender
        )

        if other_user.pk in added_users:
            continue

        added_users.add(other_user.pk)

        unread_count = DirectMessage.objects.filter(
            sender=other_user,
            receiver=current_user,
            is_read=False,
        ).count()

        conversations.append({
            "user": other_user,
            "last_message": message,
            "unread_count": unread_count,
        })

    users = Account.objects.exclude(
        pk=current_user.pk
    ).order_by("username")

    total_unread = DirectMessage.objects.filter(
        receiver=current_user,
        is_read=False,
    ).count()

    return render(request, "posts/messages.html", {
        "conversations": conversations,
        "users": users,
        "total_unread": total_unread,
    })


@login_required
def conversation(request, user_id):
    current_user = request.user
    other_user = get_object_or_404(Account, pk=user_id)

    if other_user == current_user:
        return redirect("messages")

    if not can_message_account(current_user, other_user):
        messages.error(
            request,
            "You must follow each other to message this private account.",
        )
        return redirect("messages")

    DirectMessage.objects.filter(
        sender=other_user,
        receiver=current_user,
        is_read=False,
    ).update(is_read=True)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()

        if text:
            DirectMessage.objects.create(
                sender=current_user,
                receiver=other_user,
                text=text,
            )

        return redirect("conversation", user_id=other_user.pk)

    chat_messages = (
        DirectMessage.objects
        .filter(
            Q(sender=current_user, receiver=other_user)
            | Q(sender=other_user, receiver=current_user)
        )
        .select_related("sender", "receiver")
        .order_by("created_at")
    )

    return render(request, "posts/conversation.html", {
        "other_user": other_user,
        "chat_messages": chat_messages,
    })


# =========================================================
# CREATE REEL
# =========================================================

@login_required
def create_reel(request):
    if request.method != "POST":
        return render(request, "posts/create_reel.html")

    video = request.FILES.get("video")
    caption = request.POST.get("caption", "").strip()

    if not video:
        messages.error(request, "Please select a video.")
        return redirect("create_reel")

    if not video.name.lower().endswith((".mp4", ".webm", ".mov")):
        messages.error(request, "Upload an MP4, WebM, or MOV video.")
        return redirect("create_reel")

    if video.size > 100 * 1024 * 1024:
        messages.error(request, "The maximum video size is 100 MB.")
        return redirect("create_reel")

    Reel.objects.create(
        user=request.user,
        video=video,
        caption=caption,
    )

    messages.success(request, "Your Reel was uploaded!")
    return redirect("reels")


# =========================================================
# REELS PAGE
# =========================================================

@login_required
def reels(request):
    reel_list = (
        Reel.objects
        .select_related("user")
        .prefetch_related("likes", "comments", "comments__user")
        .order_by("-created_at")
    )

    return render(request, "posts/reels.html", {
        "reels": reel_list,
        "liked_reel_ids": set(
            ReelLike.objects.filter(user=request.user)
            .values_list("reel_id", flat=True)
        ),
        "saved_reel_ids": set(
            SavedReel.objects.filter(user=request.user)
            .values_list("reel_id", flat=True)
        ),
    })


@login_required
@require_POST
def toggle_reel_like(request, reel_id):
    reel = get_object_or_404(Reel, pk=reel_id)

    like = ReelLike.objects.filter(
        user=request.user, reel=reel
    ).first()

    if like:
        like.delete()
        liked = False
    else:
        ReelLike.objects.create(user=request.user, reel=reel)
        liked = True

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes_count": reel.likes.count(),
    })


@login_required
@require_POST
def toggle_reel_save(request, reel_id):
    reel = get_object_or_404(Reel, pk=reel_id)

    saved_item = SavedReel.objects.filter(
        user=request.user, reel=reel
    ).first()

    if saved_item:
        saved_item.delete()
        saved = False
    else:
        SavedReel.objects.create(user=request.user, reel=reel)
        saved = True

    return JsonResponse({
        "success": True,
        "saved": saved,
        "reel_id": reel.pk,
    })


@login_required
@require_POST
def add_reel_comment(request, reel_id):
    reel = get_object_or_404(Reel, pk=reel_id)
    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({
            "success": False,
            "error": "Comment cannot be empty.",
        }, status=400)

    if len(text) > 500:
        return JsonResponse({
            "success": False,
            "error": "Comment must be 500 characters or fewer.",
        }, status=400)

    comment = ReelComment.objects.create(
        user=request.user,
        reel=reel,
        text=text,
    )

    return JsonResponse({
        "success": True,
        "username": request.user.get_username(),
        "text": comment.text,
        "comments_count": reel.comments.count(),
    })


@login_required
@require_POST
def delete_reel(request, reel_id):
    reel = get_object_or_404(
        Reel,
        pk=reel_id,
        user=request.user,
    )

    reel.delete()

    return JsonResponse({
        "success": True,
        "message": "Reel deleted successfully.",
    })


# =========================================================
# FOLLOW REQUESTS
# =========================================================

@login_required
def follow_requests(request):
    pending_requests = (
        FollowRequest.objects
        .filter(
            receiver=request.user,
            status=FollowRequest.PENDING,
        )
        .select_related("sender")
    )

    return render(request, "privacy/follow_requests.html", {
        "follow_requests": pending_requests,
    })


@login_required
@require_POST
def respond_follow_request(request, request_id):
    action = request.POST.get("action")

    with transaction.atomic():
        follow_request = get_object_or_404(
            FollowRequest.objects.select_for_update(),
            pk=request_id,
            receiver=request.user,
            status=FollowRequest.PENDING,
        )

        if action == "accept":
            Follow.objects.get_or_create(
                follower=follow_request.sender,
                following=request.user,
            )

            follow_request.status = FollowRequest.ACCEPTED
            follow_request.save(update_fields=["status"])

            if follow_request.sender != request.user:
                Notification.objects.create(
                    actor=request.user,
                    recipient=follow_request.sender,
                    notification_type="follow",
                )

            messages.success(
                request,
                f"Accepted @{follow_request.sender.username}.",
            )

        elif action == "reject":
            follow_request.status = FollowRequest.REJECTED
            follow_request.save(update_fields=["status"])
            messages.success(request, "Follow request rejected.")
        else:
            return JsonResponse({
                "success": False,
                "message": "Invalid action.",
            }, status=400)

    return redirect("follow_requests")


# =========================================================
# PRIVACY SETTINGS
# =========================================================

@login_required
def privacy_settings(request):
    if request.method == "POST":
        request.user.private_account = (
            request.POST.get("private_account") == "on"
        )

        request.user.save(update_fields=["private_account"])

        messages.success(
            request,
            "Your privacy settings have been updated.",
        )
        return redirect("privacy_settings")

    return render(request, "privacy/privacy_settings.html")


# =========================================================
# POST / REEL VIEW TRACKING
# =========================================================

@login_required
@require_POST
def track_post_view(request, post_id):
    post = get_object_or_404(
        Post,
        pk=post_id,
        video__isnull=True,
    )

    track_content_view(request, post)

    return JsonResponse({
        "success": True,
        "post_id": post.pk,
    })


@login_required
@require_POST
def track_reel_view(request, reel_id):
    reel = get_object_or_404(Reel, pk=reel_id)

    track_content_view(request, reel)

    return JsonResponse({
        "success": True,
        "reel_id": reel.pk,
    })
