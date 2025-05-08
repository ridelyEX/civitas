from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class data(models.Model):
    piky    = models.AutoField(primary_key=True)
    
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
        ordering = ["nombre"]
        verbose_name_plurar = "Datos"
        
    def __str__(self):
        return self.nombre
 
class soli(models.Model):
    piky   = models.AutoField(primary_key=True)
    
    asunto = models.ForeignKey(data, on_delete=models.CASCADE)

    dirr   = models.CharField(max_length=100)
    desc   = models.TextField(blank=True)
    info   = models.TextField(blank=True)
    
class SubirDocs(models.Model):
    descp = models.CharField(max_length=100)
    doc = models.FileField(upload_to='docs/')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    
    class Meta:
        db_table = 'files'
        ordering = ['-created_at']