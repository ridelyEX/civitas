FROM python:3.13-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=civitas.settings
# Apuntar fontconfig a un directorio de caché escribible por el usuario no-root
ENV FONTCONFIG_CACHE_DIR=/var/cache/fontconfig

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    mariadb-client \
    netcat-traditional \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libcairo-gobject2 \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root y el directorio de caché para fontconfig en una sola capa
RUN addgroup --system --gid 101 appgroup && \
    adduser --system --uid 101 --ingroup appgroup appuser && \
    mkdir -p $FONTCONFIG_CACHE_DIR && \
    chown -R appuser:appgroup $FONTCONFIG_CACHE_DIR

# Copiar e instalar requerimientos de python con los permisos correctos
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación y el entrypoint con los permisos correctos
COPY --chown=appuser:appgroup . .
COPY --chown=appuser:appgroup docker-entrypoint.sh /docker-entrypoint.sh

# Crear directorios para volúmenes y asegurar permisos de ejecución
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app/staticfiles /app/media && \
    chmod -R 775 /app/staticfiles /app/media && \
    chmod +x /docker-entrypoint.sh

# Cambiar al usuario no-root
USER appuser

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "civitas/gunicorn.conf.py", "civitas.wsgi:application"]