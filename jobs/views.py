from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django.db.models import F
from jobs.models import Job, JobStatus, SavedJob
from jobs.serializers import JobSerializer, JobCreateUpdateSerializer
from accounts.permissions import IsRecruiter
from recruiters.models import RecruiterProfile
from companies.models import Company


class JobListView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'company__name']
    ordering_fields = ['created_at', 'min_salary', 'views_count']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsRecruiter()]

    def get_queryset(self):
        user = self.request.user
        mine = self.request.query_params.get('mine', 'false').lower() == 'true'

        if mine and user.is_authenticated:
            return Job.objects.filter(recruiter=user).select_related('company', 'recruiter').prefetch_related('required_skills__skill')

        qs = Job.objects.filter(status=JobStatus.ACTIVE).select_related('company', 'recruiter').prefetch_related('required_skills__skill')

        # Filters
        job_type = self.request.query_params.get('type')
        if job_type:
            qs = qs.filter(job_type=job_type)

        workplace = self.request.query_params.get('workplace')
        if workplace:
            qs = qs.filter(workplace_type=workplace)

        experience = self.request.query_params.get('experience')
        if experience:
            qs = qs.filter(experience_level=experience)

        location = self.request.query_params.get('location')
        if location:
            qs = qs.filter(location__icontains=location)

        min_sal = self.request.query_params.get('min_salary')
        if min_sal:
            qs = qs.filter(min_salary__gte=min_sal)

        return qs

    def perform_create(self, serializer):
        recruiter = self.request.user
        company = None
        # Link to recruiter's assigned company
        if hasattr(recruiter, 'recruiter_profile') and recruiter.recruiter_profile.company:
            company = recruiter.recruiter_profile.company
        else:
            company, _ = Company.objects.get_or_create(
                name="TalentAI Innovators",
                defaults={'description': 'Pioneering AI-driven technology company'}
            )
        serializer.save(recruiter=recruiter, company=company)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all().select_related('company', 'recruiter').prefetch_related('required_skills__skill')
    serializer_class = JobSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsRecruiter()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count safely
        Job.objects.filter(id=instance.id).update(views_count=F('views_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SavedJobToggleView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        saved_obj, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if not created:
            saved_obj.delete()
            return Response({'saved': False, 'message': 'Job removed from saved'}, status=status.HTTP_200_OK)
        return Response({'saved': True, 'message': 'Job saved successfully'}, status=status.HTTP_201_CREATED)


class SavedJobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        saved_jobs_ids = SavedJob.objects.filter(user=self.request.user).values_list('job_id', flat=True)
        return Job.objects.filter(id__in=saved_jobs_ids).select_related('company', 'recruiter').prefetch_related('required_skills__skill')
