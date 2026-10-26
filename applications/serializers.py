from rest_framework import serializers
from applications.models import JobApplication
from jobs.serializers import JobSerializer
from accounts.serializers import UserSerializer
from resumes.serializers import ResumeSerializer


class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    job_id = serializers.IntegerField(write_only=True, required=False)
    candidate = UserSerializer(read_only=True)
    resume = ResumeSerializer(read_only=True)
    resume_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    interview_link = serializers.SerializerMethodField()
    interview_id = serializers.SerializerMethodField()

    def get_interview_link(self, obj):
        latest = obj.interviews.order_by('-scheduled_at').first()
        if latest:
            return latest.meeting_link or f"/live-interview?room=interview_{latest.id}&id={latest.id}"
        return None

    def get_interview_id(self, obj):
        latest = obj.interviews.order_by('-scheduled_at').first()
        return latest.id if latest else None

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_id', 'candidate', 'resume', 'resume_id',
            'cover_letter', 'status', 'ai_match_score', 'ai_match_explanation',
            'ai_matched_skills', 'ai_missing_skills', 'recruiter_notes',
            'interview_link', 'interview_id',
            'applied_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'candidate', 'ai_match_score', 'ai_match_explanation',
            'ai_matched_skills', 'ai_missing_skills', 'interview_link', 'interview_id',
            'applied_at', 'updated_at'
        ]


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['status', 'recruiter_notes']
