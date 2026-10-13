from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from accounts.models import Account


# =========================================================
# POST
# =========================================================


class Post(models.Model):

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='posts'
    )

    # Optional for video-only Reels
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True
    )

    # New field for Reels
    video = models.FileField(
        upload_to='posts/videos/',
        blank=True,
        null=True
    )

    caption = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def is_video(self):
        return bool(self.video)

    def __str__(self):
        return f"Post by {self.user.username}"


# =========================================================
# POST IMAGE
# =========================================================

class PostImage(models.Model):

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='posts/'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Image for Post {self.post.id}"


# =========================================================
# LIKE
# =========================================================

class Like(models.Model):

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


# =========================================================
# COMMENT
# =========================================================

class Comment(models.Model):

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Comment by {self.user.username}"

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Story(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories"
    )

    image = models.ImageField(
        upload_to="stories/images/",
        blank=True,
        null=True
    )

    video = models.FileField(
        upload_to="stories/videos/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):

        if not self.expires_at:
            self.expires_at = (
                timezone.now() +
                timedelta(hours=24)
            )

        super().save(*args, **kwargs)

    @property
    def is_active(self):

        return (
            self.expires_at and
            self.expires_at > timezone.now()
        )

    @property
    def is_video(self):

        return bool(self.video)

    def __str__(self):
        return f"{self.user.username} - Story {self.id}"


class StoryLike(models.Model):

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_likes"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_likes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["story", "user"],
                name="unique_story_like"
            )
        ]


class StoryComment(models.Model):

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_comments"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_comments"
    )

    text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class StoryView(models.Model):

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_views"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_views"
    )

    viewed_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["story", "user"],
                name="unique_story_view"
            )
        ]

# =========================================================
# FOLLOW
# =========================================================

class Follow(models.Model):

    follower = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='following'
    )

    following = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='followers'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'follower',
            'following'
        )

    def __str__(self):

        return (
            f"{self.follower.username} "
            f"follows "
            f"{self.following.username}"
        )


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_notifications'
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):

        return (
            f"{self.actor.username} "
            f"-> "
            f"{self.recipient.username} "
            f"({self.notification_type})"
        )


# =========================================================
# SAVED POST
# =========================================================

class SavedPost(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_posts'
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_saved_post'
            )
        ]

        ordering = ['-created_at']

    def __str__(self):

        return (
            f"{self.user.username} "
            f"saved post {self.post.id}"
        )


# =========================================================
# DIRECT MESSAGE
# =========================================================

class DirectMessage(models.Model):

    sender = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    text = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):

        return (
            f"{self.sender.username} -> "
            f"{self.receiver.username}"
        )


# =========================================================
# REELS
# Add below your existing models in posts/models.py
# =========================================================

from django.core.validators import FileExtensionValidator


class Reel(models.Model):
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='reels'
    )
    video = models.FileField(
        upload_to='reels/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'webm', 'mov']
            )
        ]
    )
    caption = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reel by {self.user}"


class ReelLike(models.Model):
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='reel_likes'
    )
    reel = models.ForeignKey(
        Reel,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'reel'],
                name='unique_reel_like'
            )
        ]


class ReelComment(models.Model):
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='reel_comments'
    )
    reel = models.ForeignKey(
        Reel,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user}"

# =========================================================
# SAVED REELS
# =========================================================

class SavedReel(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_reels'
    )

    reel = models.ForeignKey(
        Reel,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'reel'],
                name='unique_saved_reel'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} saved Reel {self.reel_id}"



# =========================================================
# FOLLOW REQUESTS
# =========================================================

class FollowRequest(models.Model):

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]

    sender = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sent_follow_requests'
    )

    receiver = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='received_follow_requests'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['sender', 'receiver'],
                name='unique_follow_request_pair'
            ),
        ]

    def __str__(self):
        return (
            f'{self.sender.username} -> '
            f'{self.receiver.username} ({self.status})'
        )

