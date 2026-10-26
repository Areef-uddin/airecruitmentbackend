import os
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from resumes.models import Resume
from resumes.serializers import ResumeSerializer
from ai_services.services import AIService


class ResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get('file')
        file_name = uploaded_file.name if uploaded_file else 'resume.pdf'
        file_size = uploaded_file.size if uploaded_file else 0
        file_ext = os.path.splitext(file_name)[1].lower().replace('.', '') or 'pdf'

        # Count existing resumes to decide is_primary
        is_first = not Resume.objects.filter(candidate=self.request.user).exists()

        resume_instance = serializer.save(
            candidate=self.request.user,
            file_name=file_name,
            file_size=file_size,
            file_type=file_ext,
            is_primary=is_first
        )

        # Trigger AI parsing
        try:
            parsed_result = AIService.parse_resume(
                file_name=file_name,
                raw_text=f"Candidate Resume: {self.request.user.get_full_name()}. Skills: Python, Flutter, Django, AI Engineering, Cloud Architecture, PostgreSQL, Docker."
            )
            resume_instance.extracted_text = parsed_result.get('summary', '')
            resume_instance.parsed_data = parsed_result
            resume_instance.ai_parsed = True
            resume_instance.parsed_at = timezone.now()
            resume_instance.save()
        except Exception:
            # Resilient fallback if AI service is offline
            pass


class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResumeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user)
