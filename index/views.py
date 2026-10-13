from django.shortcuts import render
from django.utils import timezone
from accounts.models import Account
from posts.models import FollowRequest
import random

from posts.models import (
    Post,
    Like,
    Follow,
    SavedPost,
    Story,
    StoryView,
    Reel,
    ReelLike,
)

def get_suggested_users(user, limit=None):
    """Return randomly selected accounts the user does not follow."""

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



def index(request):

    # =========================================================
    # POSTS
    # =========================================================

    posts = (
        Post.objects
        .select_related('user')
        .prefetch_related(
            'likes',
            'comments',
            'comments__user'
        )
        .order_by('?')
    )

    # =========================================================
    # REELS FOR THE FEED
    # =========================================================

    feed_reels = (
        Reel.objects
        .select_related('user')
        .prefetch_related(
            'likes',
            'comments',
            'comments__user'
        )
        .order_by('-created_at')
    )

    # Reels liked by the logged-in user
    liked_reel_ids = set()

    if request.user.is_authenticated:
        liked_reel_ids = set(
            ReelLike.objects
            .filter(user=request.user)
            .values_list('reel_id', flat=True)
        )

    # =========================================================
    # USER SOCIAL DATA
    # =========================================================

    liked_posts = []
    following_ids = []
    saved_post_ids = []

    if request.user.is_authenticated:

        liked_posts = list(
            Like.objects
            .filter(user=request.user)
            .values_list(
                'post_id',
                flat=True
            )
        )

        following_ids = list(
            Follow.objects
            .filter(follower=request.user)
            .values_list(
                'following_id',
                flat=True
            )
        )

        saved_post_ids = list(
            SavedPost.objects
            .filter(user=request.user)
            .values_list(
                'post_id',
                flat=True
            )
        )

    # =========================================================
    # ACTIVE STORIES
    # =========================================================

    now = timezone.now()

    # Remove expired stories
    Story.objects.filter(
        expires_at__lte=now
    ).delete()

    # Get active stories
    active_stories = list(
        Story.objects
        .filter(
            expires_at__gt=now
        )
        .select_related('user')
        .order_by('-created_at')
    )

    # =========================================================
    # STORIES VIEWED BY CURRENT USER
    # =========================================================

    viewed_story_ids = set()

    if request.user.is_authenticated:

        viewed_story_ids = set(
            StoryView.objects
            .filter(
                user=request.user,
                story__expires_at__gt=now
            )
            .values_list(
                'story_id',
                flat=True
            )
        )

    # =========================================================
    # GROUP ALL STORIES BY USER
    # =========================================================

    stories_by_user = {}

    for story in active_stories:

        user_id = story.user_id

        if user_id not in stories_by_user:
            stories_by_user[user_id] = []

        stories_by_user[user_id].append(story)

    # =========================================================
    # CREATE STORY GROUPS
    # =========================================================

    story_groups = []

    for user_id, user_stories in stories_by_user.items():

        if not user_stories:
            continue

        # A user is unseen if at least one story is unviewed
        has_unseen = any(
            story.id not in viewed_story_ids
            for story in user_stories
        )

        # Find newest unseen story
        unseen_stories = [
            story
            for story in user_stories
            if story.id not in viewed_story_ids
        ]

        latest_unseen_story = (
            unseen_stories[0]
            if unseen_stories
            else None
        )

        story_groups.append({
            'user': user_stories[0].user,
            'stories': user_stories,
            'latest_story': user_stories[0],
            'has_unseen': has_unseen,
            'latest_unseen_story': latest_unseen_story,
        })

    # =========================================================
    # STORY ORDER
    # 1. USERS WITH UNSEEN STORIES - RANDOM
    # 2. USERS WITH ALL STORIES VIEWED - RANDOM
    # =========================================================

    unseen_story_groups = [
        group
        for group in story_groups
        if group['has_unseen']
    ]

    seen_story_groups = [
        group
        for group in story_groups
        if not group['has_unseen']
    ]

    # Randomly shuffle unseen users
    random.shuffle(unseen_story_groups)

    # Randomly shuffle completely viewed users
    random.shuffle(seen_story_groups)

    # Unseen users remain before seen users
    story_groups = (
        unseen_story_groups
        + seen_story_groups
    )

    # =========================================================
    # CURRENT USER STORIES
    # =========================================================

    my_stories = []
    my_story_group = None

    if request.user.is_authenticated:

        for group in story_groups:

            if group['user'].id == request.user.id:

                my_story_group = group
                my_stories = group['stories']

                break

    # =========================================================
    # OTHER USERS' STORIES
    # =========================================================

    other_story_groups = []

    for group in story_groups:

        # Don't show current user's story in other users section
        if (
            request.user.is_authenticated
            and group['user'].id == request.user.id
        ):
            continue

        other_story_groups.append(group)

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        # POSTS
        'posts': posts,

        # REELS
        'feed_reels': feed_reels,
        'liked_reel_ids': liked_reel_ids,

        # POST SOCIAL DATA
        'liked_posts': liked_posts,
        'following_ids': following_ids,
        'saved_post_ids': saved_post_ids,

         # PEOPLE YOU MAY KNOW — RANDOM 5 USERS
        'sidebar_suggested_users': get_suggested_users(
            request.user, limit=5
        ),
        'suggested_users': get_suggested_users(
            request.user, limit=5
        ),


        # STORIES
        'stories': active_stories,
        'my_stories': my_stories,
        'my_story_group': my_story_group,
        'story_groups': story_groups,
        'other_story_groups': other_story_groups,

        # IDs OF STORIES ALREADY VIEWED
        'viewed_story_ids': viewed_story_ids,
    }

    return render(
        request,
        'index.html',
        context
    )



# =========================================================
# STORY CONTEXT HELPER
# =========================================================

def get_story_context(request):

    now = timezone.now()

    # ---------------------------------------------------------
    # REMOVE EXPIRED STORIES
    # ---------------------------------------------------------

    Story.objects.filter(
        expires_at__lte=now
    ).delete()

    # ---------------------------------------------------------
    # GET ACTIVE STORIES
    # ---------------------------------------------------------

    active_stories = list(
        Story.objects
        .filter(
            expires_at__gt=now
        )
        .select_related('user')
        .order_by('-created_at')
    )

    # =========================================================
    # OWN STORIES
    # =========================================================

    my_stories = []

    if request.user.is_authenticated:

        my_stories = [
            story
            for story in active_stories
            if story.user_id == request.user.id
        ]

    # =========================================================
    # VIEWED STORY IDS
    # =========================================================

    viewed_story_ids = set()

    if request.user.is_authenticated:

        viewed_story_ids = set(
            StoryView.objects
            .filter(
                user=request.user,
                story__expires_at__gt=now
            )
            .values_list(
                'story_id',
                flat=True
            )
        )

    # =========================================================
    # GROUP OTHER USERS' STORIES
    # =========================================================

    groups = {}

    for story in active_stories:

        # Don't include own stories
        if (
            request.user.is_authenticated
            and story.user_id == request.user.id
        ):
            continue

        if story.user_id not in groups:

            groups[story.user_id] = {
                'user': story.user,
                'stories': [],
                'has_unseen': False,
                'latest_created_at': story.created_at,
                'latest_unseen_created_at': None,
            }

        group = groups[story.user_id]

        group['stories'].append(story)

        # -----------------------------------------------------
        # CHECK IF STORY HAS NOT BEEN VIEWED
        # -----------------------------------------------------

        if story.id not in viewed_story_ids:

            group['has_unseen'] = True

            if (
                group['latest_unseen_created_at'] is None
                or story.created_at
                > group['latest_unseen_created_at']
            ):

                group['latest_unseen_created_at'] = (
                    story.created_at
                )

    # =========================================================
    # INSTAGRAM-STYLE STORY ORDER
    # =========================================================

    unseen_story_groups = [
        group
        for group in groups.values()
        if group['has_unseen']
    ]

    seen_story_groups = [
        group
        for group in groups.values()
        if not group['has_unseen']
    ]

    # Randomly shuffle unseen users
    random.shuffle(unseen_story_groups)

    # Randomly shuffle viewed users
    random.shuffle(seen_story_groups)

    # Unseen users remain first
    other_story_groups = (
        unseen_story_groups
        + seen_story_groups
    )

    return {
        'my_stories': my_stories,
        'other_story_groups': other_story_groups,
        'viewed_story_ids': viewed_story_ids,
    }


def portfolio(request):
    return render(request, "portfolio.html")

