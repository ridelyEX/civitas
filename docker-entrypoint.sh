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
import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civitas.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
      cursor.execute(\"SHOW TABLES\")
      tables = cursor.fetchall()
      print('yes' if tables else 'no')
except Exception as e:
    print(f'Error de conexión a la base de datos: {e}')
    print('no')
" 2>/dev/null)

if [ "$DB_INITIALIZED" = "no" ]; then
  echo "Primera inicialización de base de datos"

  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find . -path "*/migrations/*.pyc" -delete

  echo "Creando migraciones"
  python manage.py makemigrations

  # Ejecutar migraciones
  echo "Ejecutando migraciones..."
  python manage.py migrate --noinput


  # Crear superusuario si no existe
  echo "Creando superusuario..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
from datetime import date
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123'),
        first_name='Admin',
        last_name='Sistema',
        bday=date(1990, ,1),
    )
    print('Superusuario creado')
else:
  print('usuario existente')
"
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