from django.db import models
from django.conf import settings
from applications.models import JobApplication


class InterviewType(models.TextChoices):
    AI_SCREENING = 'AI_SCREENING', 'AI Live Screening'
    TECHNICAL = 'TECHNICAL', 'Technical Interview'
    BEHAVIORAL = 'BEHAVIORAL', 'Behavioral & Culture'
    EXECUTIVE = 'EXECUTIVE', 'Executive Round'


class InterviewStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class OverallDecision(models.TextChoices):
    STRONG_YES = 'STRONG_YES', 'Strong Hire'
    YES = 'YES', 'Hire'
    NEUTRAL = 'NEUTRAL', 'Neutral'
    NO = 'NO', 'Do Not Hire'
    STRONG_NO = 'STRONG_NO', 'Strong Reject'


class Interview(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    title = models.CharField(max_length=200, default='AI Technical Screening')
    interview_type = models.CharField(max_length=30, choices=InterviewType.choices, default=InterviewType.AI_SCREENING)
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_interviews',
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    meeting_link = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=30, choices=InterviewStatus.choices, default=InterviewStatus.SCHEDULED)
    ai_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True, default='')
    ai_transcript = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"{self.interview_type} for {self.application.candidate.email}"


class InterviewFeedback(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='feedbacks')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_feedbacks')
    technical_rating = models.IntegerField(default=4)  # 1-5
    communication_rating = models.IntegerField(default=4)
    culture_fit_rating = models.IntegerField(default=4)
    overall_decision = models.CharField(max_length=20, choices=OverallDecision.choices, default=OverallDecision.YES)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.reviewer.email} on {self.interview.id}"
