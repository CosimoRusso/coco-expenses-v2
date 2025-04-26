from django.db import models


class User(models.Model):
    email = models.EmailField(
        verbose_name="E-mail",
        unique=True,
        error_messages={
            "blank": "Campo richiesto.",
            "unique": "Indirizzo e-mail già registrato.",
        },
    )
    email_confirmed_at = models.DateTimeField(
        verbose_name="E-mail confirmed at", null=True
    )
    password_hash = models.CharField(verbose_name="Password", max_length=128)
    first_name = models.CharField(verbose_name="First Name", max_length=128)
    last_name = models.CharField(verbose_name="Last name", max_length=128)
