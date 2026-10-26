from django.db import models
from django.conf import settings
from companies.models import Company


class RecruiterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='recruiters')
    title = models.CharField(max_length=150, default='Talent Acquisition Lead')
    department = models.CharField(max_length=120, default='People & Culture')
    phone = models.CharField(max_length=30, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        company_name = self.company.name if self.company else 'Independent'
        return f"Recruiter: {self.user.get_full_name() or self.user.email} ({company_name})"
