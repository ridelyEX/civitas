from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import AutoField

from portaldu.desUr.models import Files


class CustomUser(BaseUserManager):
    def create_user(self, usuario, email, password=None, **extra_fields):

        if not email:
            raise ValueError("Ingrese email")
        if not usuario:
            raise ValueError("ingresar usuario")
        email = self.normalize_email(email)
        user = self.model(usuario=usuario, email=email, **extra_fields)
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

    class Meta:
        db_table = 'cmin_users'
        ordering = ['usuario']

    def __str__(self):
        return self.usuario


class LoginDate(models.Model):
    login_ID = models.AutoField(primary_key=True)
    user_FK = models.ForeignKey(users, on_delete=models.CASCADE, verbose_name='usuarios')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'LoginDate'
        ordering = ['user_FK']

    def __str__(self):
        return self.date

class SolicitudesPendientes(models.Model):
    solicitud_ID = models.AutoField(primary_key=True)
    nomSolicitud = models.CharField(max_length=150)
    fechaSolicitud = models.DateField()
    doc_FK = models.ForeignKey(Files, on_delete=models.CASCADE, verbose_name='documentos')

    class Meta:
        db_table = 'SolicitudesPendientes'
        ordering = ['solicitud_ID']

    def __str__(self):
        return self.nomSolicitud


class SolicitudesEnviadas(models.Model):
    solicitud_ID = AutoField(primary_key=True)
    nomSolicitud = models.CharField(max_length=150)
    fechaEnvio = models.DateField(auto_now=True)
    user_FK = models.ForeignKey(users, on_delete=models.CASCADE, verbose_name='usuarios')
    doc_FK = models.ForeignKey(Files, on_delete=models.CASCADE, verbose_name='documentos')
    solicitud_FK = models.ForeignKey(SolicitudesPendientes, on_delete=models.CASCADE, verbose_name='solicitudes')

    class Meta:
        db_table = 'SolicitudesEnviadas'
        ordering = ['solicitud_ID']

    def __str__(self):
        return self.nomSolicitud
# Create your models here.
