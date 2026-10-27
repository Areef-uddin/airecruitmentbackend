from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from applications.models import JobApplication, ApplicationStatus
from applications.serializers import JobApplicationSerializer, ApplicationStatusUpdateSerializer
from jobs.models import Job
from resumes.models import Resume
from notifications.models import Notification, NotificationType
from ai_services.services import AIService


class ApplyJobView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        candidate = request.user

        # Prevent duplicate applications
        if JobApplication.objects.filter(job=job, candidate=candidate).exists():
            return Response(
                {'error': 'You have already submitted an application for this position.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume_id = request.data.get('resume_id')
        uploaded_resume_file = request.FILES.get('resume') or request.FILES.get('file')
        resume = None

        if uploaded_resume_file:
            import os
            from django.utils import timezone
            file_name = uploaded_resume_file.name
            file_size = uploaded_resume_file.size
            file_ext = os.path.splitext(file_name)[1].lower().replace('.', '') or 'pdf'

            raw_text = ""
            try:
                uploaded_resume_file.seek(0)
                if file_ext == 'pdf':
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_resume_file)
                    pages_text = [page.extract_text() or '' for page in reader.pages]
                    raw_text = "\n".join(pages_text).strip()
                elif file_ext in ['txt', 'md']:
                    raw_text = uploaded_resume_file.read().decode('utf-8', errors='ignore')
                uploaded_resume_file.seek(0)
            except Exception:
                pass

            if not raw_text:
                raw_text = f"Candidate: {candidate.get_full_name() or candidate.email}. Professional Technical Applicant for {job.title}."

            resume = Resume.objects.create(
                candidate=candidate,
                file=uploaded_resume_file,
                file_name=file_name,
                file_size=file_size,
                file_type=file_ext,
                is_primary=True
            )
            try:
                parsed_result = AIService.parse_resume(
                    file_name=file_name,
                    raw_text=raw_text
                )
                resume.parsed_data = parsed_result
                resume.extracted_text = raw_text[:5000] if raw_text else parsed_result.get('summary', '')
                resume.ai_parsed = True
                resume.parsed_at = timezone.now()
                resume.save()
            except Exception:
                pass
        elif resume_id:
            resume = Resume.objects.filter(id=resume_id, candidate=candidate).first()

        if not resume:
            resume = Resume.objects.filter(candidate=candidate, is_primary=True).first() or Resume.objects.filter(candidate=candidate).first()

        cover_letter = request.data.get('cover_letter', '')

        # Calculate AI match score & rationale
        match_analysis = AIService.match_candidate_to_job(
            candidate_user=candidate,
            job=job,
            resume=resume
        )

        app = JobApplication.objects.create(
            job=job,
            candidate=candidate,
            resume=resume,
            cover_letter=cover_letter,
            status=ApplicationStatus.SUBMITTED,
            ai_match_score=match_analysis.get('match_score', 84.0),
            ai_match_explanation=match_analysis.get('explanation', 'Strong overall qualification match.'),
            ai_matched_skills=match_analysis.get('matched_skills', []),
            ai_missing_skills=match_analysis.get('missing_skills', [])
        )

        # Notify Recruiter
        if job.recruiter:
            Notification.objects.create(
                user=job.recruiter,
                title=f"New Applicant for {job.title}",
                message=f"{candidate.get_full_name() or candidate.email} just applied with an AI match score of {app.ai_match_score}%.",
                notification_type=NotificationType.APPLICATION_UPDATE,
                link=f"/recruiter/applications/{app.id}"
            )

        # Notify Candidate
        Notification.objects.create(
            user=candidate,
            title="Application Submitted",
            message=f"Your application for {job.title} at {job.company.name} was successfully delivered.",
            notification_type=NotificationType.APPLICATION_UPDATE,
            link=f"/candidate/applications/{app.id}"
        )

        return Response(JobApplicationSerializer(app).data, status=status.HTTP_201_CREATED)


class ApplicationListView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        job_id = self.request.query_params.get('job_id')
        status_filter = self.request.query_params.get('status')

        if user.is_candidate:
            qs = JobApplication.objects.filter(candidate=user).select_related('job', 'job__company', 'resume', 'candidate')
        elif user.is_recruiter or user.is_super_admin:
            if user.is_super_admin:
                qs = JobApplication.objects.all().select_related('job', 'job__company', 'resume', 'candidate')
            else:
                qs = JobApplication.objects.filter(job__recruiter=user).select_related('job', 'job__company', 'resume', 'candidate')
        else:
            qs = JobApplication.objects.none()

        if job_id:
            qs = qs.filter(job_id=job_id)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.order_by('-applied_at')


class ApplicationDetailView(generics.RetrieveAPIView):
    queryset = JobApplication.objects.all().select_related('job', 'job__company', 'resume', 'candidate')
    serializer_class = JobApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'

    def perform_update(self, serializer):
        app = serializer.save()
        # Notify candidate on status change
        Notification.objects.create(
            user=app.candidate,
            title=f"Application Update: {app.job.title}",
            message=f"Your application status has been updated to '{app.get_status_display()}'.",
            notification_type=NotificationType.APPLICATION_UPDATE,
            link=f"/candidate/applications/{app.id}"
        )
