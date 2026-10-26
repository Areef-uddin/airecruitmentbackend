from rest_framework import generics, permissions, status
from rest_framework.response import Response
from accounts.models import User, UserRole
from companies.models import Company
from jobs.models import Job, JobStatus
from applications.models import JobApplication
from interviews.models import Interview
from ai_services.models import AIAnalysis
from audit_logs.models import AuditLog
from accounts.permissions import IsSuperAdmin


class AdminDashboardView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        total_users = User.objects.count()
        total_candidates = User.objects.filter(role=UserRole.CANDIDATE).count()
        total_recruiters = User.objects.filter(role=UserRole.RECRUITER).count()

        total_companies = Company.objects.count()
        verified_companies = Company.objects.filter(is_verified=True).count()

        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(status=JobStatus.ACTIVE).count()

        total_applications = JobApplication.objects.count()
        interviews_count = Interview.objects.count()
        ai_analyses_count = AIAnalysis.objects.count()

        recent_users = User.objects.order_by('-date_joined')[:10]
        recent_users_data = [
            {
                'id': u.id,
                'email': u.email,
                'name': u.get_full_name() or u.username,
                'role': u.role,
                'is_active': u.is_active,
                'date_joined': u.date_joined.strftime('%Y-%m-%d %H:%M')
            }
            for u in recent_users
        ]

        recent_logs = AuditLog.objects.order_by('-timestamp')[:10]
        recent_logs_data = [
            {
                'id': log.id,
                'user': log.user.email if log.user else 'System',
                'action': log.action,
                'entity_type': log.entity_type,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for log in recent_logs
        ]

        return Response({
            'overview': {
                'total_users': total_users,
                'total_candidates': total_candidates,
                'total_recruiters': total_recruiters,
                'total_companies': total_companies,
                'verified_companies': verified_companies,
                'active_jobs': active_jobs,
                'total_jobs': total_jobs,
                'total_applications': total_applications,
                'interviews_conducted': interviews_count,
                'ai_requests_processed': ai_analyses_count,
                'system_health': '99.98% Normal',
            },
            'recent_users': recent_users_data,
            'recent_logs': recent_logs_data
        }, status=status.HTTP_200_OK)


class AdminUserManagementView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        data = [
            {
                'id': u.id,
                'email': u.email,
                'name': u.get_full_name() or u.username,
                'role': u.role,
                'is_active': u.is_active,
                'date_joined': u.date_joined.strftime('%Y-%m-%d'),
            }
            for u in users
        ]
        return Response({'results': data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is not None:
            user.is_active = is_active
            user.save(update_fields=['is_active'])

        return Response({'message': f'User {user.email} updated', 'is_active': user.is_active})
