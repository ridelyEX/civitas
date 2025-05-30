from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUser(BaseUserManager):
    def create_user(self, usuario, nombre, correo, contrasena):

        user_data = {
            'usuario':usuario,
            'nombre':nombre,
            'correo':correo,
            'contrasena':contrasena,
        }

        if contrasena:
            user_data['contrasena'] = self.make_random_password()

        db_table = 'users'
        user_data.save()

        return user_data

class users(models.Model):
    user_ID = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, verbose_name="Nombre")
    apellidos = models.CharField(max_length=50, verbose_name="Apellidos")
    correo = models.EmailField(max_length=50)
    usuario = models.CharField(max_length=30)


    class Meta:
        db_table = 'users'
        ordering = ["user_ID"]
        verbose_name = "Usuarios"

    def __str__(self):
        return str(self.user_ID)

# Create your models here.
