from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class data(models.Model):
    piKy= models.AutoField(primary_key=True)
    
    nombre  = models.CharField(max_length=100, verbose_name="Nombre")
    pApe    = models.CharField(max_length=100, verbose_name="Apellido Paterno")
    mApe    = models.CharField(max_length=100, verbose_name="Apellido Materno")
    bDay    = models.DateField()
    asunto  = models.CharField(max_length=100)
    tel     = PhoneNumberField(region="MX")
    curp    = models.CharField(max_length=18)
    sexo    = models.CharField(max_length=10)
    dirr    = models.CharField(max_length=100)
    
    class meta():
        db_table = 'desur_data'
        ordering = ["nombre"]
        verbose_name_plurar = "Datos"
        
    def __str__(self):
        return self.nombre

class soli(models.Model):
    piSoliKy   = models.AutoField(primary_key=True)
    fDataKy = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="Datos")
    dirr   = models.CharField(max_length=100)
    descc   = models.TextField(blank=True)
    info   = models.TextField(blank=True)
    
    class Meta():
        db_table = 'desur_soli'
        ordering = ["fDataKy"]
    
    def __str__(self):
        return self.asunto


class SubirDocs(models.Model):
    nombre = models.CharField(max_length=100)
    descp = models.CharField(max_length=100)
    doc = models.FileField(upload_to='docs/')
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        db_table = 'files'
        ordering = ['fecha']