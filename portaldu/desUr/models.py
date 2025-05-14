from django.db import models
from django.db.models import AutoField
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Uuid(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)


class data(models.Model):
    data_ID = models.AutoField(primary_key=True)
    uuid = models.ForeignKey(Uuid, on_delete=models.CASCADE,
                                verbose_name="ides")
    nombre  = models.CharField(max_length=30, verbose_name="Nombre")
    pApe    = models.CharField(max_length=30, verbose_name="Apellido Paterno")
    mApe    = models.CharField(max_length=30, verbose_name="Apellido Materno")
    bDay    = models.DateField()
    asunto  = models.CharField(max_length=30)
    tel     = PhoneNumberField(region="MX")
    curp    = models.CharField(max_length=18)
    sexo    = models.CharField(max_length=10)
    dirr    = models.CharField(max_length=50)

    class Meta:
        db_table = 'dataT'
        get_latest_by = 'data_ID'
        ordering = ["data_ID"]
        verbose_name = "Datos"

    def __str__(self):
        return self.nombre

class users(models.Model):
    user_ID = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, verbose_name="Nombre")
    apellidos = models.CharField(max_length=50, verbose_name="Apellidos")
    correo = models.CharField(max_length=50)
    usuario = models.CharField(max_length=30)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="Datos", default=0)

    class Meta:
        db_table = 'users'
        ordering = ["user_ID"]
        verbose_name = "Usuarios"

    def __str__(self):
        return self.user_ID




class SubirDocs(models.Model):
    doc_ID = AutoField(primary_key=True)
    nomDoc = models.CharField(max_length=50, null=True, blank=True)
    descDoc = models.CharField(max_length=100)
    doc = models.FileField(upload_to='documents/')
    fechaDoc = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'files'
        ordering = ['fechaDoc']
        verbose_name = "Documentos"

    def __str__(self):
        return self.nomDoc


class Contador(models.Model):
    count_ID = models.AutoField(primary_key=True)
    count = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'contador'
        ordering = ['count']

    def __str__(self):
        return self.count



class soli(models.Model):
    soli_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="Datos")
    doc_ID = models.ForeignKey(SubirDocs, on_delete=models.CASCADE, verbose_name="Documentos",
                               blank=True, null=True)
    dirr   = models.CharField(max_length=50)
    descc   = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    info   = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'soli'
        ordering = ["data_ID"]
        verbose_name = "Solicitud"

    def __str__(self):
        return self.data_ID

    #def save(self, *args, **kwargs):
     #   if not self.data_ID_id and data.objects.exists():
      #      self.data_ID_id = data.objects.latest('data_ID').data_ID
      #  super().save(*args, **kwargs)

