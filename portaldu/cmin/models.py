from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class CustomUser(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("Ingrese email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class users(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    usuario = models.CharField(max_length=100, unique=True)
    bday = models.DateField()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['nombre']

    objects = CustomUser()

    def __str__(self):
        return self.nombre


class LoginDate(models.Model):
    date = models.DateTimeField(default=timezone.now)
# Create your models here.
