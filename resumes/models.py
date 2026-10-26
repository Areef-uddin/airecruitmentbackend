from django.db import models
from django.conf import settings


class Resume(models.Model):
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    file_type = models.CharField(max_length=20, default='pdf')
    extracted_text = models.TextField(blank=True, default='')
    parsed_data = models.JSONField(default=dict, blank=True)
    is_primary = models.BooleanField(default=False)
    ai_parsed = models.BooleanField(default=False)
    parsed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.is_primary:
            Resume.objects.filter(candidate=self.candidate, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.candidate.email} - {self.file_name}"
