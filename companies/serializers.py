from rest_framework import serializers
from companies.models import Company, CompanyMembership
from accounts.serializers import UserSerializer


class CompanySerializer(serializers.ModelSerializer):
    active_jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'logo', 'logo_url', 'website',
            'description', 'industry', 'company_size', 'headquarters',
            'is_verified', 'verification_date', 'active_jobs_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'is_verified', 'verification_date', 'created_at', 'updated_at']

    def get_active_jobs_count(self, obj):
        from jobs.models import JobStatus
        return obj.jobs.filter(status=JobStatus.ACTIVE).count()


class CompanyMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ['id', 'company', 'user', 'role', 'joined_at']
