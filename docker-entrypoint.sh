#!/bin/bash
set -e

# Función para esperar a que un servicio esté disponible
wait_for_service() {
    local host="$1"
    local port="$2"
    local max_attempts=60
    local attempt=1

    echo "Esperando a que $host:$port esté disponible..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$host:$port está disponible"
            return 0
        fi

        echo "Intento $attempt/$max_attempts: $host:$port no está disponible, esperando..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "Error: $host:$port no está disponible después de $max_attempts intentos"
    exit 1
}

# Función para verificar conectividad de red
check_network() {
    echo "Verificando conectividad de red..."
    if ! command -v nc >/dev/null 2>&1; then
        echo "Error: netcat no está instalado"
        exit 1
    fi

    # Verificar si podemos hacer ping al host
    if ! getent hosts db >/dev/null 2>&1; then
        echo "Error: No se puede resolver el hostname 'db'"
        echo "Hosts disponibles en /etc/hosts:"
        cat /etc/hosts
        exit 1
    fi
}

# Verificar red
check_network

# Esperar a MySQL
echo "Esperando a MySQL..."
wait_for_service db 3306

# Esperar a Redis
echo "Esperando a Redis..."
wait_for_service redis 6379

# Verificar conexión a la base de datos
echo "Verificando conexión a la base de datos..."
DB_INITIALIZED=$(python -c "
import os
import pymysql

try:
    connection = pymysql.connect(
      host='db',
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD'),
      database=os.getenv('DB_NAME'),
      port=3306
    )

    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    connection.close()
    print('yes' if result else 'no')
except Exception as e:
    print(f'Error de conexión a la base de datos: {e}')
    print('no')
" 2>/dev/null || echo 'no')

if [ "$DB_INITIALIZED" = "no" ]; then
  echo "Primera inicialización de base de datos"

  # Solo eliminar migraciones de nuestras aplicaciones, no de Django ni librerías
  find ./portaldu -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./portaldu -path "*/migrations/*.pyc" -delete

  echo "Creando migraciones en orden específico para resolver dependencias"

  # Primero crear desUr que no tiene dependencias externas
  echo "Creando migraciones para desUr (modelos base)..."
  python manage.py makemigrations desUr

  # Luego crear cmin que depende de desUr
  echo "Creando migraciones para cmin (con referencias a desUr)..."
  python manage.py makemigrations cmin

  # Finalmente verificar si hay migraciones adicionales
  echo "Verificando migraciones adicionales..."
  python manage.py makemigrations

  # Ejecutar migraciones en orden correcto
  echo "Ejecutando migraciones..."
  echo "Aplicando migraciones de Django core..."
  python manage.py migrate contenttypes --noinput
  python manage.py migrate auth --noinput

  echo "Aplicando migraciones de desUr..."
  python manage.py migrate desUr --noinput

  echo "Aplicando migraciones de cmin..."
  python manage.py migrate cmin --noinput

  echo "Aplicando migraciones restantes..."
  python manage.py migrate --noinput

  # Solo crear superusuario si este es el contenedor web (ejecutando gunicorn)
  if [ "$1" = "gunicorn" ]; then
    echo "Creando superusuario (solo desde contenedor web)..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
from datetime import date
try:
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(
            username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
            email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
            password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123'),
            first_name='Admin',
            last_name='Sistema',
            bday=date(1990, 1, 1),
        )
        print('Superusuario creado')
    else:
        print('Superusuario ya existe')
except Exception as e:
    print(f'Error al crear superusuario: {e}')
"
  else
    echo "Contenedor worker/beat - saltando creación de superusuario"
  fi
else
    echo "Base de datos existente"

    echo "Aplicando migraciones pendientes"
    python manage.py migrate --noinput || {
      echo "Error con las migraciones, corriendo fake-initial"
      python manage.py migrate --fake-initial
    }
fi
# Colectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando aplicación..."
# Ejecutar el comando pasado como argumento
exec "$@"