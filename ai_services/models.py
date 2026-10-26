from django.db import models
from django.conf import settings


class AIAnalysisType(models.TextChoices):
    RESUME_PARSE = 'RESUME_PARSE', 'Resume Parsing'
    CANDIDATE_MATCH = 'CANDIDATE_MATCH', 'Candidate Matching'
    JOB_GEN = 'JOB_GEN', 'Job Description Generation'
    QUESTION_GEN = 'QUESTION_GEN', 'Interview Question Generation'
    ASSISTANT = 'ASSISTANT', 'Recruitment Assistant Chat'
    INTERVIEW_EVAL = 'INTERVIEW_EVAL', 'Interview Evaluation'


class AIAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    analysis_type = models.CharField(max_length=40, choices=AIAnalysisType.choices)
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)
    score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='SUCCESS')
    execution_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analysis_type} ({self.status}) @ {self.created_at}"
