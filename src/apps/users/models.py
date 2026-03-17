from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=50,
        verbose_name="Ник",
        unique=True,
    )
    email = models.EmailField(unique=True, verbose_name="E-mail")
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Номер телефона",
    )

    def __str__(self):
        return self.username
