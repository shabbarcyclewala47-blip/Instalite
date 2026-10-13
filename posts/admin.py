from django.contrib import admin

from .models import Post, Like, Comment, Story, Follow


# =========================
# POST ADMIN
# =========================

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'caption',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'user__username',
        'caption',
    )

    ordering = (
        '-created_at',
    )


# =========================
# LIKE ADMIN
# =========================

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'post',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'user__username',
    )


# =========================
# COMMENT ADMIN
# =========================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'post',
        'text',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'user__username',
        'text',
    )


# =========================
# STORY ADMIN
# =========================

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'created_at',
        'expires_at',
        'is_active',
    )

    list_filter = (
        'created_at',
        'expires_at',
    )

    search_fields = (
        'user__username',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'created_at',
    )


# =========================
# FOLLOW ADMIN
# =========================

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'follower',
        'following',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'follower__username',
        'following__username',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'created_at',
    )