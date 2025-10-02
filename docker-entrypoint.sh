#!/bin/bash
set -e

# Función para esperar a que un servicio esté disponible
wait_for_service() {
    host="$1"
    port="$2"
    echo "Esperando a que $host:$port esté disponible..."
    while ! nc -z "$host" "$port"; do
        sleep 1
    done
    echo "$host:$port está disponible"
}

# Esperar a los servicios dependientes
if [ "$DATABASE_URL" ]; then
    wait_for_service db 5432
fi

if [ "$REDIS_URL" ]; then
    wait_for_service redis 6379
fi

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Colectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    )
    print('Superusuario creado')
EOF

# Ejecutar el comando pasado como argumento
exec "$@"