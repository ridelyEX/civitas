from django.db import models
from django.db.models import AutoField
from django.forms import FileField
from phonenumber_field.modelfields import PhoneNumberField
import uuid



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
    disc    = models.CharField(max_length=30, verbose_name="discapacidad")
    etnia   = models.CharField(max_length=30, verbose_name="etnia")

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


class Contador(models.Model):
    count_ID = models.AutoField(primary_key=True)
    count = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'contador'
        ordering = ['count']

    def __str__(self):
        return self.count or 0

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
    dirr   = models.TextField()
    descc   = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    info   = models.TextField(blank=True, null=True)
    puo = models.CharField(max_length=50, null=True, blank=True)
    foto = models.ImageField(upload_to = 'fotos', null=True, blank=True)

    class Meta:
        db_table = 'soli'
        ordering = ["data_ID"]
        verbose_name = "Solicitud"

    def __str__(self):
        return str(self.soli_ID)

class Files(models.Model):
    fDoc_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    finalDoc = models.FileField(upload_to='solicitudes')
    nomDoc = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'solicitudes'
        ordering = ['fDoc_ID']
        verbose_name = "solicitudes"



