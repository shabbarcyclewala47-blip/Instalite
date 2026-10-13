from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # POSTS
    # =====================================================

    path(
        'create/',
        views.create_post,
        name='create_post'
    ),

    path(
        'feed/',
        views.feed,
        name='feed'
    ),

    path(
        'delete/<int:post_id>/',
        views.delete_post,
        name='delete_post'
    ),

    path(
        'like/<int:post_id>/',
        views.like_post,
        name='like_post'
    ),

    path(
        'comment/<int:post_id>/',
        views.add_comment,
        name='add_comment'
    ),

    path(
        'follow/<int:user_id>/',
        views.follow_user,
        name='follow_user'
    ),

    path(
        'save/<int:post_id>/',
        views.save_post,
        name='save_post'
    ),


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    path(
        'notifications/',
        views.notifications,
        name='notifications'
    ),

    path(
        'notifications/read/',
        views.mark_notifications_read,
        name='mark_notifications_read'
    ),


    # =====================================================
    # SAVED / LIKED POSTS
    # =====================================================

    path(
        'saved/',
        views.saved_posts,
        name='saved_posts'
    ),

    path(
        'liked/',
        views.liked_posts,
        name='liked_posts'
    ),


    # =====================================================
    # STORIES
    # =====================================================

    path(
        'story/create/',
        views.create_story,
        name='create_story'
    ),

    path(
        'stories/',
        views.stories,
        name='stories'
    ),

    


    # =====================================================
    # PROFILE
    # =====================================================

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),

    path(
    'profile/<int:user_id>/',
    views.public_profile,
    name='public_profile'
    ),


    # =====================================================
    # MESSAGES
    # =====================================================

    path(
        'messages/',
        views.messages_inbox,
        name='messages'
    ),

    path(
        'messages/<int:user_id>/',
        views.conversation,
        name='conversation'
    ),

    path(
    'search-users/',
    views.search_users,
    name='search_users'
    ),

    path("explore/", views.explore, name="explore"),

    path(
    "story/like/<int:story_id>/",
    views.like_story,
    name="like_story"
    ),

    path(
    "story/data/<int:story_id>/",
    views.story_interaction_data,
    name="story_interaction_data"
    ),


    path(
    "story/view/<int:story_id>/",
    views.view_story,
    name="view_story"
    ),

    path(
    "story/comment/<int:story_id>/",
    views.comment_story,
    name="comment_story"
    ),

    path(
    "story/share/<int:story_id>/",
    views.share_story,
    name="share_story"
    ),

    path(
    "story/delete/<int:story_id>/",
    views.delete_story,
    name="delete_story"
    ),


    path(
    'reels/',
    views.reels,
    name='reels'
    ),

    path(
    'reels/create/',
    views.create_reel,
    name='create_reel'
    ),
    path(
        'reels/<int:reel_id>/like/',
        views.toggle_reel_like,
        name='toggle_reel_like'
    ),
    path(
        'reels/<int:reel_id>/comment/',
        views.add_reel_comment,
        name='add_reel_comment'
    ),

    
    path(
    "reel/delete/<int:reel_id>/",
    views.delete_reel,
    name="delete_reel"
    ),
    
    path(
    'reels/<int:reel_id>/save/',
    views.toggle_reel_save,
    name='toggle_reel_save'
    ),
    
# =====================================================
# PRIVACY AND FOLLOW REQUESTS
# =====================================================

    path(
    'privacy/',
    views.privacy_settings,
    name='privacy_settings'
    ),

    path(
    'follow-requests/',
    views.follow_requests,
    name='follow_requests'
    ),

    path(
    'follow-requests/<int:request_id>/respond/',
    views.respond_follow_request,
    name='respond_follow_request'
    ),


    path(
    'reels/<int:reel_id>/track-view/',
    views.track_reel_view,
    name='track_reel_view'
    ),

    path(
    'posts/<int:post_id>/track-view/',
    views.track_post_view,
    name='track_post_view'
    ),

    
    path(
    'people-you-may-know/',
    views.people_you_may_know,
    name='people_you_may_know'
    ),


   

    



   




    
]