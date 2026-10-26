from django.db import models
from django.conf import settings
from companies.models import Company
from candidates.models import Skill


class JobType(models.TextChoices):
    FULL_TIME = 'FULL_TIME', 'Full-time'
    PART_TIME = 'PART_TIME', 'Part-time'
    CONTRACT = 'CONTRACT', 'Contract'
    INTERNSHIP = 'INTERNSHIP', 'Internship'


class WorkplaceType(models.TextChoices):
    REMOTE = 'REMOTE', 'Remote'
    HYBRID = 'HYBRID', 'Hybrid'
    ONSITE = 'ONSITE', 'On-site'


class ExperienceLevel(models.TextChoices):
    ENTRY = 'ENTRY', 'Entry Level'
    MID = 'MID', 'Mid Level'
    SENIOR = 'SENIOR', 'Senior'
    LEAD = 'LEAD', 'Lead / Staff'
    EXECUTIVE = 'EXECUTIVE', 'Executive / Director'


class JobStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    ACTIVE = 'ACTIVE', 'Active'
    PAUSED = 'PAUSED', 'Paused'
    CLOSED = 'CLOSED', 'Closed'


class Job(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    description = models.TextField()
    responsibilities = models.TextField(blank=True, default='')
    requirements = models.TextField(blank=True, default='')
    benefits = models.TextField(blank=True, default='')
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    workplace_type = models.CharField(max_length=20, choices=WorkplaceType.choices, default=WorkplaceType.REMOTE)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.MID)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    location = models.CharField(max_length=255, default='Remote')
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.ACTIVE, db_index=True)
    views_count = models.PositiveIntegerField(default=0)
    ai_generated_description = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company.name}"


class JobSkill(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='required_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='job_associations')
    is_mandatory = models.BooleanField(default=True)
    minimum_years = models.FloatField(default=1.0)

    class Meta:
        unique_together = ('job', 'skill')

    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"
