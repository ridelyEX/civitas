from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import AutoField
from django.forms import FileField
from django.urls import reverse

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


class Notifications(models.Model):
    notification_ID = models.AutoField(primary_key=True)
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    msg = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


    class Meta:
        db_table = 'Notificaciones'
        ordering = ['-notification_ID']

    def __str__(self):
        return self.msg or "Notificación sin mensaje"


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

#Encuesta flutter
class EncuestasOffline(models.Model):
    encuesta_ID = models.AutoField(primary_key=True)
    f_uuid = models.CharField(blank=True, null=True, max_length=100)
    fecha_respuesta = models.CharField(max_length=100, blank=True, null=True)
    escuela = models.CharField(max_length=255, blank=True, null=True)
    colonia = models.CharField(max_length=255, blank=True, null=True)
    rol_social = models.CharField(max_length=255, blank=True, null=True)
    genero = models.CharField(max_length=100, blank=True, null=True)
    nivel_escolar = models.CharField(max_length=100, blank=True, null=True)
    grado_escolar = models.CharField(max_length=100, blank=True, null=True)
    comunidad_indigena = models.CharField(max_length=100, blank=True, null=True)
    otro_comunidad_indigena = models.CharField(max_length=100, blank=True, null=True)
    grupo_vulnerable = models.CharField(max_length=100, blank=True, null=True)
    otro_grupo_vulnerable = models.CharField(max_length=100, blank=True, null=True)
    tipo_proyecto = models.CharField(max_length=100, blank=True, null=True)
    pregunta_1 = models.IntegerField(blank=True, null=True)
    pregunta_2 = models.CharField(max_length=255, blank=True, null=True)
    otro_pregunta_2 = models.CharField(max_length=255, blank=True, null=True)
    pregunta_3 = models.CharField(max_length=255 ,blank=True, null=True)
    pregunta_4 = models.IntegerField(blank=True, null=True)
    pregunta_5 = models.CharField(max_length=255, blank=True, null=True)
    pregunta_6 = models.IntegerField(blank=True, null=True)
    pregunta_7 = models.IntegerField(blank=True, null=True)
    pregunta_8 = models.IntegerField(blank=True, null=True)
    pregunta_9 = models.IntegerField(blank=True, null=True)
    pregunta_10 = models.IntegerField(blank=True, null=True)
    pregunta_11 = models.IntegerField(blank=True, null=True)
    pregunta_12 = models.CharField(max_length=255, blank=True, null=True)
    otro_pregunta_12 = models.CharField(max_length=255, blank=True, null=True)
    pregunta_13 = models.IntegerField(blank=True, null=True)
    pregunta_14 = models.IntegerField(blank=True, null=True)
    pregunta_15 = models.CharField(max_length=255, blank=True, null=True)
    otro_pregunta_15 = models.CharField(max_length=255, blank=True, null=True)
    pregunta_16 = models.CharField(max_length=255, blank=True, null=True)
    otro_pregunta_16 = models.CharField(max_length=255, blank=True, null=True)
    pregunta_17 = models.CharField(max_length=255, blank=True, null=True)
    confirmacion = models.CharField(max_length=10, blank=True, null=True)
    foto_url = models.CharField(max_length=255, blank=True, null=True)
    sincronizado = models.IntegerField(default=0)
    completada = models.IntegerField(default=0)
    created_at = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.CharField(max_length=100, blank=True, null=True)

    
class EncuestasOnline(models.Model):
    encuesta_ID = models.AutoField(primary_key=True)
    usuario_ID = models.CharField(max_length=100, blank=True, null=True)
    f_uuid = models.CharField(blank=True, null=True, max_length=100)
    fecha_respuesta = models.CharField(max_length=100, blank=True, null=True)
    completada = models.IntegerField(default=0)
    respuestas = models.TextField(blank=True, null=True)
    encuesta_FK = models.ForeignKey('EncuestaModel', on_delete=models.CASCADE, verbose_name='encuesta')

    class Meta:
        db_table = 'encuestas_online'
        ordering = ['-encuesta_ID']
        verbose_name = "Encuesta Online"

    def __str__(self):
        return f"Encuesta {self.encuesta_ID} - Usuario {self.usuario_ID}"

class EncuestaModel(models.Model):
    encuesta_ID = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255 , blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.CharField(max_length=100, blank=True, null=True)
    activa = models.IntegerField(default=1)
    preguntas = models.TextField(blank=True, null=True)  # JSON o texto con las preguntas de la encuesta

    class Meta:
        db_table = 'encuesta'
        ordering = ['-fecha_creacion']
        verbose_name = "Encuesta"

    def __str__(self):
        return self.nombre
# Create your models here.
