from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    SYSTEM = 'SYSTEM', 'System'
    APPLICATION_UPDATE = 'APPLICATION_UPDATE', 'Application Update'
    INTERVIEW_INVITE = 'INTERVIEW_INVITE', 'Interview Invite'
    AI_MATCH = 'AI_MATCH', 'AI Match'
    JOB_ALERT = 'JOB_ALERT', 'Job Alert'


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"
