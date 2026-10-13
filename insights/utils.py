
from .models import ContentView


def track_content_view(request, obj):
    if not request.session.session_key:
        request.session.create()

    viewer = (
        request.user
        if request.user.is_authenticated
        else None
    )

    lookup = {
        "content_type__app_label": obj._meta.app_label,
        "content_type__model": obj._meta.model_name,
        "object_id": obj.pk,
    }

    if viewer:
        already_viewed = ContentView.objects.filter(
            **lookup,
            viewer=viewer,
        ).exists()
    else:
        already_viewed = ContentView.objects.filter(
            **lookup,
            session_key=request.session.session_key,
            viewer__isnull=True,
        ).exists()

    if not already_viewed:
        ContentView.objects.create(
            content_object=obj,
            viewer=viewer,
            session_key=request.session.session_key,
        )
