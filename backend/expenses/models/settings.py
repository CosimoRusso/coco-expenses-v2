from django.db import models


class Settings(models.Model):
    max_categories = models.PositiveIntegerField(null=True, blank=True)
    max_trips = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Settings (max_categories={self.max_categories}, max_trips={self.max_trips})"

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"
