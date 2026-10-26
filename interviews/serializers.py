from rest_framework import serializers
from interviews.models import Interview, InterviewFeedback
from applications.serializers import JobApplicationSerializer
from accounts.serializers import UserSerializer


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = InterviewFeedback
        fields = ['id', 'interview', 'reviewer', 'technical_rating', 'communication_rating', 'culture_fit_rating', 'overall_decision', 'comments', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']


class InterviewSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    application_id = serializers.IntegerField(write_only=True, required=False)
    interviewer = UserSerializer(read_only=True)
    feedbacks = InterviewFeedbackSerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'application_id', 'title', 'interview_type',
            'interviewer', 'scheduled_at', 'duration_minutes', 'meeting_link',
            'status', 'ai_score', 'ai_feedback', 'ai_transcript', 'feedbacks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'interviewer', 'created_at', 'updated_at']
