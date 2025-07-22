from django.db import models
from django.db.models import AutoField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.conf import settings
import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Ingrese email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class DesUrUsers(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    bday = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='fotos', null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    # Agregando related_name únicos para evitar conflictos con cmin.Users
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='desur_users_set',
        related_query_name='desur_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='desur_users_set',
        related_query_name='desur_user',
    )

    class Meta:
        db_table = 'desur_users'
        ordering = ['username']

    def __str__(self):
        return self.username


class DesUrLoginDate(models.Model):
    login_ID = models.AutoField(primary_key=True)
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DesUrLoginDate'
        ordering = ['user_FK']

    def __str__(self):
        return str(self.date)

    @classmethod
    def create(cls, user):
        return cls.objects.create(
            user_FK=user
        )


class Uuid(models.Model):
    prime =  models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    class Meta:
        db_table: 'uuid'
        ordering = ["uuid"]

    def __str__(self):
        return str(self.uuid)


class data(models.Model):
    data_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="ides")
    nombre  = models.CharField(max_length=30, verbose_name="Nombre")
    pApe    = models.CharField(max_length=30, verbose_name="Apellido Paterno")
    mApe    = models.CharField(max_length=30, verbose_name="Apellido Materno")
    bDay    = models.DateField()
    asunto  = models.CharField(max_length=30)
    tel     = PhoneNumberField(region="MX")
    curp    = models.CharField(max_length=18)
    sexo    = models.CharField(max_length=10)
    dirr    = models.TextField()
    disc    = models.CharField(max_length=100, verbose_name="discapacidad")
    etnia   = models.CharField(max_length=100, verbose_name="etnia")
    vul     = models.CharField(max_length=100, verbose_name="vulnerabilidad")

    class Meta:
        db_table = 'dataT'
        get_latest_by = 'data_ID'
        ordering = ["data_ID"]
        verbose_name = "Datos"

    def __str__(self):
        return self.nombre

    #def save(self, *args, **kwargs):
     #   if not self.fuuid and Uuid.objects.exists():
      #      self.fuuid = Uuid.objects.latest('uuid')
       # super().save(*args, **kwargs)


class SubirDocs(models.Model):
    doc_ID = AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    nomDoc = models.CharField(max_length=50, null=True, blank=True)

    descDoc = models.CharField(max_length=100)
    doc = models.FileField(upload_to='documents/')
    fechaDoc = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'files'
        ordering = ['fechaDoc']
        verbose_name = "Documentos"

    def __str__(self):
        return self.nomDoc or "Documento sin nombre"


class Pagos(models.Model):
    pago_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="datos")
    fecha = models.DateTimeField(null = True, blank = True)
    pfm = models.CharField(max_length=80, null = True, blank = True)

    class Meta:
        db_table = 'pagos'
        ordering = ['pago_ID']

    def __str__(self):
        return self.pfm or ""

    def save(self, *args, **kwargs):
        if not self.data_ID_id and data.objects.exists():
            self.data_ID_id = data.objects.latest('data_ID').data_ID
        super().save(*args, **kwargs)

class soli(models.Model):
    soli_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="Datos")
    doc_ID = models.ForeignKey(SubirDocs, on_delete=models.CASCADE, verbose_name="Documentos",
                                blank=True, null=True)
    # Agregar referencia al empleado que procesó el trámite
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   verbose_name="Procesado por", null=True, blank=True)
    dirr   = models.TextField()
    calle = models.CharField(max_length=50, null=True, blank=True)
    colonia = models.CharField(max_length=50, null=True, blank=True)
    cp = models.CharField(max_length=5, null=True, blank=True)
    descc   = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    info   = models.TextField(blank=True, null=True)
    puo = models.CharField(max_length=50, null=True, blank=True)
    foto = models.ImageField(upload_to = 'fotos', null=True, blank=True)
    folio = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'soli'
        ordering = ["data_ID"]
        verbose_name = "Solicitud"

    def __str__(self):
        return str(self.soli_ID)

class Files(models.Model):
    fDoc_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    finalDoc = models.FileField(upload_to='solicitudes/')
    nomDoc = models.CharField(max_length=255, null=True, blank=True)
    soli_FK = models.ForeignKey(soli, on_delete=models.CASCADE)

    class Meta:
        db_table = 'solicitudes'
        ordering = ['fDoc_ID']
        verbose_name = "solicitudes"

    def __str__(self):
        return str(self.nomDoc)
