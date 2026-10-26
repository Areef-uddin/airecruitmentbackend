from django.db import models


class PlatformMetric(models.Model):
    metric_date = models.DateField(unique=True)
    total_candidates = models.PositiveIntegerField(default=0)
    total_recruiters = models.PositiveIntegerField(default=0)
    active_jobs = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    interviews_conducted = models.PositiveIntegerField(default=0)
    avg_match_score = models.FloatField(default=0.0)
    ai_analyses_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-metric_date']

    def __str__(self):
        return f"Metrics for {self.metric_date}"
