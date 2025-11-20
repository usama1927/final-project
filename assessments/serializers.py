from rest_framework import serializers

from .models import Response


class AudioUploadSerializer(serializers.Serializer):
    audio = serializers.FileField()


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = [
            "id",
            "question",
            "transcription",
            "score",
            "feedback_text",
            "wer",
            "ai_metadata",
        ]

