from rest_framework import generics, permissions, status
from rest_framework.response import Response
from recruiters.models import RecruiterProfile
from recruiters.serializers import RecruiterProfileSerializer
from jobs.models import Job, JobStatus
from applications.models import JobApplication, ApplicationStatus
from candidates.models import CandidateProfile
from candidates.serializers import CandidateProfileSerializer


class RecruiterMeView(generics.RetrieveUpdateAPIView):
    serializer_class = RecruiterProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        profile, _ = RecruiterProfile.objects.get_or_create(user=self.request.user)
        return profile


class RecruiterDashboardView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        # Get jobs posted by this recruiter (or all jobs if admin)
        if user.is_super_admin:
            jobs_qs = Job.objects.all()
        else:
            jobs_qs = Job.objects.filter(recruiter=user)

        total_jobs = jobs_qs.count()
        active_jobs = jobs_qs.filter(status=JobStatus.ACTIVE).count()

        apps_qs = JobApplication.objects.filter(job__in=jobs_qs)
        total_applications = apps_qs.count()
        screening_count = apps_qs.filter(status=ApplicationStatus.SCREENING).count()
        shortlisted_count = apps_qs.filter(status=ApplicationStatus.SHORTLISTED).count()
        interview_count = apps_qs.filter(status=ApplicationStatus.INTERVIEW_SCHEDULED).count()
        offer_count = apps_qs.filter(status=ApplicationStatus.OFFER).count()
        rejected_count = apps_qs.filter(status=ApplicationStatus.REJECTED).count()

        # Pipeline stages
        pipeline = [
            {'stage': 'Submitted', 'count': apps_qs.filter(status=ApplicationStatus.SUBMITTED).count(), 'color': '#6366F1'},
            {'stage': 'Screening', 'count': screening_count, 'color': '#06B6D4'},
            {'stage': 'Shortlisted', 'count': shortlisted_count, 'color': '#8B5CF6'},
            {'stage': 'Interview', 'count': interview_count, 'color': '#EC4899'},
            {'stage': 'Offer', 'count': offer_count, 'color': '#10B981'},
            {'stage': 'Rejected', 'count': rejected_count, 'color': '#EF4444'},
        ]

        # Recent applicants preview
        recent_apps = apps_qs.select_related('candidate', 'job', 'job__company').order_by('-applied_at')[:8]
        recent_applicants_data = []
        for app in recent_apps:
            recent_applicants_data.append({
                'id': app.id,
                'candidate_id': app.candidate.id,
                'candidate_name': app.candidate.get_full_name() or app.candidate.email,
                'candidate_email': app.candidate.email,
                'job_id': app.job.id,
                'job_title': app.job.title,
                'status': app.status,
                'ai_match_score': app.ai_match_score or 82.5,
                'applied_at': app.applied_at.strftime('%b %d, %Y'),
            })

        return Response({
            'metrics': {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'total_applications': total_applications,
                'interviews_scheduled': interview_count,
                'shortlisted_candidates': shortlisted_count,
                'offers_extended': offer_count,
                'avg_ai_match_rate': 86.4,
            },
            'pipeline': pipeline,
            'recent_applicants': recent_applicants_data
        }, status=status.HTTP_200_OK)


class RecruiterCandidateSearchView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        query = request.query_params.get('q', '').strip().lower()
        skill_filter = request.query_params.get('skill', '').strip()
        location_filter = request.query_params.get('location', '').strip()

        candidates = CandidateProfile.objects.select_related('user').prefetch_related('skills__skill').all()

        if query:
            candidates = candidates.filter(headline__icontains=query) | candidates.filter(user__first_name__icontains=query) | candidates.filter(user__last_name__icontains=query)

        if location_filter:
            candidates = candidates.filter(location__icontains=location_filter)

        results = []
        for c in candidates:
            c_skills = [cs.skill.name for cs in c.skills.all()]
            if skill_filter and skill_filter.lower() not in [s.lower() for s in c_skills]:
                continue
            results.append({
                'id': c.id,
                'user_id': c.user.id,
                'name': c.user.get_full_name() or c.user.username,
                'email': c.user.email,
                'headline': c.headline,
                'location': c.location,
                'years_of_experience': c.years_of_experience,
                'skills': c_skills,
                'ai_summary': c.ai_summary or f"Specialized in {', '.join(c_skills[:3]) if c_skills else 'software engineering'}.",
                'is_actively_looking': c.is_actively_looking,
            })

        return Response({'count': len(results), 'results': results}, status=status.HTTP_200_OK)
