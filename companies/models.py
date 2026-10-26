from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    industry = models.CharField(max_length=120, default='Technology')
    company_size = models.CharField(max_length=50, default='50-200 employees')
    headquarters = models.CharField(max_length=255, default='San Francisco, CA')
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MembershipRole(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    ADMIN = 'ADMIN', 'Admin'
    RECRUITER = 'RECRUITER', 'Recruiter'
    VIEWER = 'VIEWER', 'Viewer'


class CompanyMembership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_memberships')
    role = models.CharField(max_length=20, choices=MembershipRole.choices, default=MembershipRole.RECRUITER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.role})"
