# create_simple_admin.py - Script independiente para crear admin
import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civitas.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_admin():
    User = get_user_model()

    # Verificar si ya existe
    if User.objects.filter(username='admin').exists():
        print("✅ Usuario 'admin' ya existe")
        return

    # Crear el usuario administrador
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@civitas.com',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema',
        rol='administrador'
    )

    # Darle permisos de superusuario
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.is_active = True
    admin_user.save()

    print("🎉 Usuario administrador creado!")
    print("Username: admin")
    print("Password: admin123")
    print("⚠️  Cambia la contraseña después del primer login")

if __name__ == '__main__':
    create_admin()