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

    def create_user(self, creator_user, email, password=None, is_staff=False, is_superuser=False,**extra_fields):
        if not creator_user.can_create_user_type(is_staff, is_superuser):
            user_type = "superusuario" if is_superuser else "staff" if is_staff else "otra cosa"
            raise PermissionError(f"No tienes permisos para crear un {user_type}")

        extra_fields['is_staff'] = is_staff
        extra_fields['is_superuser'] = is_superuser
        return self.create_user(email, password, **extra_fields)

    def get_superusers(self):
        return self.filter(is_superuser=True)

    def get_staff(self):
        return self.filter(is_staff=False, is_superuser=False)

    def get_regular(self):
        return self.filter(is_staff=False, is_superuser=False)

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

    @property
    def get_user_type(self):
        if self.is_superuser:
            return'Superman'
        elif self.is_staff:
            return 'Staff'
        else:
            return 'Regular'

    def can_create_user_type(self, target_is_staff, target_is_superuser):
        if self.is_superuser:
            return True
        elif self.is_staff:
            return not target_is_staff and not target_is_superuser
        else:
            return False

    def get_allowed_user(self):
        if self.is_superuser:
            return[
                ('superuser', 'Superusuario'),
                ('staff','Staff'),
                ('user','Invitado'),
            ]
        elif self.is_staff:
            return [('user', 'Invitado')]
        else:
            return []

    def can_manage_users(self):
        return self.is_superuser or self.is_staff

    def get_manageable_user(self):
        if self.is_superuser:
            return Users.objects.all()
        elif self.is_staff:
            return Users.objects.filter(is_staff=False, is_superuser=False)
        else:
            return Users.objects.none()


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
    PRIORIDAD_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
    ]


    solicitud_ID = AutoField(primary_key=True)
    nomSolicitud = models.CharField(max_length=150)
    fechaEnvio = models.DateField(auto_now=True)
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    doc_FK = models.ForeignKey(Files, on_delete=models.CASCADE, verbose_name='documentos')
    solicitud_FK = models.ForeignKey(SolicitudesPendientes, on_delete=models.CASCADE, verbose_name='solicitudes')
    folio = models.CharField(max_length=50, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='Media')

    usuario_asignado = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_asignadas', verbose_name='Usuario Asignado'
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('completado', 'Completado')
        ],
        default='pendiente'
    )

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
