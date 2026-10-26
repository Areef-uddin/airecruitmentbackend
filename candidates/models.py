from django.db import models
from django.conf import settings


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=80, default='Technical')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProficiencyLevel(models.TextChoices):
    BEGINNER = 'BEGINNER', 'Beginner'
    INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
    ADVANCED = 'ADVANCED', 'Advanced'
    EXPERT = 'EXPERT', 'Expert'


class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    headline = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    location = models.CharField(max_length=150, blank=True, default='San Francisco, CA')
    years_of_experience = models.FloatField(default=0.0)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    current_company = models.CharField(max_length=150, blank=True, default='')
    notice_period_days = models.IntegerField(default=30)
    portfolio_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    github_url = models.URLField(blank=True, default='')
    is_actively_looking = models.BooleanField(default=True)
    ai_summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Candidate: {self.user.get_full_name() or self.user.email}"


class CandidateSkill(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='candidate_associations')
    years_experience = models.FloatField(default=1.0)
    proficiency = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.INTERMEDIATE,
    )

    class Meta:
        unique_together = ('candidate', 'skill')

    def __str__(self):
        return f"{self.candidate.user.email} - {self.skill.name} ({self.proficiency})"
