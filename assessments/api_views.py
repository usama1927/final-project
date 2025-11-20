from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attempt, Response as ResponseModel
from .serializers import AudioUploadSerializer, ResponseSerializer
from .services import evaluate_response


class AudioUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, attempt_id: int, question_id: int):
        serializer = AudioUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = get_object_or_404(Attempt, pk=attempt_id)
        if attempt.student != request.user and not request.user.is_teacher():
            return Response(status=status.HTTP_403_FORBIDDEN)

        response = get_object_or_404(
            ResponseModel,
            attempt=attempt,
            question_id=question_id,
        )

        audio_file = serializer.validated_data["audio"]
        filename = default_storage.save(f"responses/audio/{audio_file.name}", audio_file)
        response.raw_audio.name = filename
        response.save(update_fields=["raw_audio"])

        evaluate_response(response)

        data = ResponseSerializer(response).data
        return Response(data, status=status.HTTP_201_CREATED)

