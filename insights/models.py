from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ContentView(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey(
        "content_type",
        "object_id"
    )

    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instalite_content_views"
    )

    session_key = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id"]
            ),
            models.Index(fields=["viewed_at"]),
        ]

    def __str__(self):
        return f"View: {self.content_type} #{self.object_id}"
