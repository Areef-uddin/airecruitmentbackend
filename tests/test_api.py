from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, UserRole
from companies.models import Company
from jobs.models import Job, JobType, WorkplaceType, ExperienceLevel, JobStatus
from applications.models import JobApplication, ApplicationStatus
from candidates.models import CandidateProfile


class AuthenticationAndRoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.candidate_user = User.objects.create_user(
            email='candidate_test@talentai.io',
            username='candidate_test',
            password='password123',
            role=UserRole.CANDIDATE
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter_test@talentai.io',
            username='recruiter_test',
            password='password123',
            role=UserRole.RECRUITER
        )
        self.company = Company.objects.create(name="Innovate Corp", industry="Tech")

    def test_user_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'candidate_test@talentai.io',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_user_login_invalid_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'candidate_test@talentai.io',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_application_and_duplicate_prevention(self):
        job = Job.objects.create(
            title="Senior Python Engineer",
            company=self.company,
            recruiter=self.recruiter_user,
            description="Build great software",
            status=JobStatus.ACTIVE
        )

        # Authenticate candidate
        self.client.force_authenticate(user=self.candidate_user)

        # First apply should succeed
        res1 = self.client.post(f'/api/applications/apply/{job.id}/', {'cover_letter': 'Excited to apply!'})
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_match_score', res1.data)

        # Duplicate apply to same job must fail with 400
        res2 = self.client.post(f'/api/applications/apply/{job.id}/', {'cover_letter': 'Duplicate apply'})
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res2.data)

    def test_recruiter_dashboard_access(self):
        self.client.force_authenticate(user=self.recruiter_user)
        response = self.client.get('/api/recruiter/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', response.data)
        self.assertIn('pipeline', response.data)

    def test_ai_generate_job_description(self):
        self.client.force_authenticate(user=self.recruiter_user)
        response = self.client.post('/api/ai/generate-job-description/', {
            'title': 'AI Solutions Architect',
            'experience_level': 'Senior',
            'workplace_type': 'Remote',
            'skills': ['Python', 'Docker', 'PyTorch']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('description', response.data)
        self.assertIn('responsibilities', response.data)
