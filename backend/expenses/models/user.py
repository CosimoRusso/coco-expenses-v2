import bcrypt
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

    def check_password(self, password):
        return check_password(password, self.password_hash)

    def is_authenticated(self):
        return True

    def __str__(self):
        return self.email


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)
