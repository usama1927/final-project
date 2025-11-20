from django.urls import path

from .api_views import AudioUploadAPIView

urlpatterns = [
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/audio/",
        AudioUploadAPIView.as_view(),
        name="api-audio-upload",
    ),
]

