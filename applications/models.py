from django.db import models
from django.conf import settings
from jobs.models import Job
from resumes.models import Resume


class ApplicationStatus(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted'
    SCREENING = 'SCREENING', 'In Screening'
    SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
    INTERVIEW_SCHEDULED = 'INTERVIEW_SCHEDULED', 'Interview Scheduled'
    OFFER = 'OFFER', 'Offer Extended'
    REJECTED = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'


class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    cover_letter = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
        db_index=True,
    )
    ai_match_score = models.FloatField(null=True, blank=True)
    ai_match_explanation = models.TextField(blank=True, default='')
    ai_matched_skills = models.JSONField(default=list, blank=True)
    ai_missing_skills = models.JSONField(default=list, blank=True)
    recruiter_notes = models.TextField(blank=True, default='')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.candidate.email} -> {self.job.title} ({self.status})"
