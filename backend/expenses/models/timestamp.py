from django.db import models


class TimestampModel(models.Model):
    # Added by Django to every model; the type stubs do not know about it.
    id: int
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
