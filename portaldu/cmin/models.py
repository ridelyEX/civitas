from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import AutoField
from django.forms import FileField

from portaldu.desUr.models import Files


class CustomUser(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("Ingrese email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Users(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    bday = models.DateField()
    foto = models.ImageField(upload_to='fotos')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUser()

    class Meta:
        db_table = 'cmin_users'
        ordering = ['username']

    def __str__(self):
        return self.username


class LoginDate(models.Model):
    login_ID = models.AutoField(primary_key=True)
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'LoginDate'
        ordering = ['user_FK']

    def __str__(self):
        return self.date

    @classmethod
    def create(cls, user):
        return cls.objects.create(
            user_FK=user
        )


class SolicitudesPendientes(models.Model):
    solicitud_ID = models.AutoField(primary_key=True)
    nomSolicitud = models.CharField(max_length=150)
    fechaSolicitud = models.DateField()
    doc_FK = models.ForeignKey(Files, on_delete=models.CASCADE, verbose_name='documentos')
    destinatario = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'SolicitudesPendientes'
        ordering = ['solicitud_ID']

    def __str__(self):
        return self.nomSolicitud


class SolicitudesEnviadas(models.Model):
    solicitud_ID = AutoField(primary_key=True)
    nomSolicitud = models.CharField(max_length=150)
    fechaEnvio = models.DateField(auto_now=True)
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    doc_FK = models.ForeignKey(Files, on_delete=models.CASCADE, verbose_name='documentos')
    solicitud_FK = models.ForeignKey(SolicitudesPendientes, on_delete=models.CASCADE, verbose_name='solicitudes')
    folio = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'SolicitudesEnviadas'
        ordering = ['solicitud_ID']

    def __str__(self):
        return self.nomSolicitud

class Seguimiento(models.Model):
    seguimiento_ID = models.AutoField(primary_key=True)
    solicitud_FK = models.ForeignKey(SolicitudesEnviadas, on_delete=models.CASCADE, verbose_name='solicitudes')
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    fechaSeguimiento = models.DateField(auto_now_add=True)
    comentario = models.TextField()
    documento = models.FileField(upload_to='seguimiento_docs/')
    nomSeg = models.CharField(max_length=200)

    class Meta:
        db_table = 'Seguimiento'
        ordering = ['seguimiento_ID']

    def __str__(self):
        return f"Seguimiento {self.seguimiento_ID} - {self.solicitud_FK.nomSolicitud}"

class Close(models.Model):
    close_ID = models.AutoField(primary_key=True)
    solicitud_FK = models.ForeignKey(SolicitudesEnviadas, on_delete=models.CASCADE, verbose_name='solicitudes')
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    seguimiento_FK = models.ForeignKey(Seguimiento, on_delete=models.CASCADE, verbose_name='seguimiento')
    fechaCierre = models.DateField(auto_now_add=True)
    comentario = models.TextField()

    class Meta:
        db_table = 'Close'
        ordering = ['close_ID']

    def __str__(self):
        return f"Cierre {self.close_ID} - {self.solicitud_FK.nomSolicitud}"


#Excel
class Licitaciones(models.Model):
    licitacion_ID = models.AutoField(primary_key=True)
    fecha_limite = models.DateField(blank=True, null=True)
    no_licitacion = models.CharField(max_length=15, blank=True, null=True)
    desc_licitacion = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'licitaciones'
        ordering = ['no_licitacion']
        verbose_name = "Licitación"

    def __str__(self):
        return self.no_licitacion or "Licitación sin número"

# Create your models here.
