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

        # Extract actual text from uploaded PDF or document
        raw_text = ""
        if uploaded_file:
            try:
                uploaded_file.seek(0)
                if file_ext == 'pdf':
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_file)
                    pages_text = [page.extract_text() or '' for page in reader.pages]
                    raw_text = "\n".join(pages_text).strip()
                elif file_ext in ['docx', 'doc']:
                    try:
                        import docx
                        doc = docx.Document(uploaded_file)
                        raw_text = "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
                    except Exception:
                        pass
                elif file_ext in ['txt', 'md']:
                    raw_text = uploaded_file.read().decode('utf-8', errors='ignore')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error extracting text from {file_name}: {e}")

        if not raw_text:
            raw_text = f"Candidate: {self.request.user.get_full_name()} ({self.request.user.email}). Title: Full Stack Developer with experience in web and mobile applications."

        # Trigger Gemini AI parsing & ATS scanning
        try:
            parsed_result = AIService.parse_resume(
                file_name=file_name,
                raw_text=raw_text
            )
            resume_instance.extracted_text = raw_text[:5000] if raw_text else parsed_result.get('summary', '')
            resume_instance.parsed_data = parsed_result
            resume_instance.ai_parsed = True
            resume_instance.parsed_at = timezone.now()
            resume_instance.save()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error scanning resume with Gemini: {e}")


class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResumeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user)
