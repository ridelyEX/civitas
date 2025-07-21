#!/bin/bash
# Script de despliegue para producción

echo "🚀 Iniciando despliegue en producción..."

# 1. Crear usuario de base de datos
echo "📊 Configurando base de datos..."
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS civitas_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'civitas_user'@'localhost' IDENTIFIED BY 'CAMBIAR_PASSWORD';
GRANT ALL PRIVILEGES ON civitas_prod.* TO 'civitas_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# 2. Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p logs
mkdir -p staticfiles
mkdir -p media/{documents,fotos,seguimiento_docs,solicitudes}

# 3. Configurar permisos
echo "🔐 Configurando permisos..."
chmod 755 media/
chmod 755 logs/
chown -R www-data:www-data media/ logs/ staticfiles/

# 4. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 5. Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate --settings=civitas.settings_production

# 6. Recopilar archivos estáticos
echo "📂 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=civitas.settings_production

# 7. Crear superusuario (si no existe)
echo "👤 Configurando usuario administrador..."
python manage.py shell --settings=civitas.settings_production << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@tucorreo.com', 'password_seguro')
    print('✅ Superusuario creado')
else:
    print('ℹ️ Superusuario ya existe')
EOF

echo "✅ Despliegue completado!"
echo "🔗 Recuerda configurar tu servidor web (Nginx/Apache)"
echo "🔒 Cambiar todas las contraseñas por defecto"
