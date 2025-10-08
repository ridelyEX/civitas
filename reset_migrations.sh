#!/bin/bash
# Script de emergencia para resetear migraciones corruptas

echo "=== SCRIPT DE EMERGENCIA PARA RESETEAR MIGRACIONES ==="
echo "ADVERTENCIA: Este script eliminará todas las migraciones y recreará la base de datos"
echo "Presiona CTRL+C para cancelar en los próximos 5 segundos..."
sleep 5

# Eliminar solo archivos de migraciones de nuestras aplicaciones
echo "Eliminando migraciones de aplicaciones del proyecto..."
find ./portaldu -path "*/migrations/*.py" -not -name "__init__.py" -exec rm -f {} \;
find ./portaldu -path "*/migrations/*.pyc" -exec rm -f {} \;
find ./portaldu -path "*/migrations/__pycache__" -exec rm -rf {} \; 2>/dev/null || true

echo "Creando nuevas migraciones..."

# Crear migraciones en orden específico
echo "1. Creando migraciones base para desUr..."
python manage.py makemigrations desUr

echo "2. Creando migraciones para cmin (que depende de desUr)..."
python manage.py makemigrations cmin

echo "3. Verificando migraciones adicionales..."
python manage.py makemigrations

echo "4. Mostrando plan de migraciones..."
python manage.py showmigrations

echo "=== MIGRACIONES RECREADAS EXITOSAMENTE ==="
echo "Ahora puedes ejecutar: python manage.py migrate"
