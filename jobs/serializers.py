from rest_framework import serializers
from jobs.models import Job, JobSkill, SavedJob
from companies.serializers import CompanySerializer
from accounts.serializers import UserSerializer
from candidates.models import Skill


class JobSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.ReadOnlyField(source='skill.name')

    class Meta:
        model = JobSkill
        fields = ['id', 'skill', 'skill_name', 'is_mandatory', 'minimum_years']


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True, required=False)
    recruiter = UserSerializer(read_only=True)
    required_skills = JobSkillSerializer(many=True, read_only=True)
    applications_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'company_id', 'recruiter',
            'description', 'responsibilities', 'requirements', 'benefits',
            'job_type', 'workplace_type', 'experience_level',
            'min_salary', 'max_salary', 'currency', 'location',
            'status', 'views_count', 'applications_count',
            'ai_generated_description', 'required_skills', 'is_saved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recruiter', 'views_count', 'created_at', 'updated_at']

    def get_applications_count(self, obj):
        return obj.applications.count()

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedJob.objects.filter(user=request.user, job=obj).exists()
        return False


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    skills_list = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'description', 'responsibilities',
            'requirements', 'benefits', 'job_type', 'workplace_type',
            'experience_level', 'min_salary', 'max_salary', 'currency',
            'location', 'status', 'ai_generated_description', 'skills_list'
        ]

    def create(self, validated_data):
        skills_data = validated_data.pop('skills_list', [])
        job = Job.objects.create(**validated_data)
        for skill_name in skills_data:
            skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
            JobSkill.objects.create(job=job, skill=skill)
        return job
