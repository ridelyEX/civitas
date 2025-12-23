# AGEO - Atención, gestión inteligente

**Versión**: 1.0.0  
**Proyecto**: AGEO 2025
**Framework**: Django 4.2+ | Python 3.11+
**Estado**: Test

---

## Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Módulos del Sistema](#-módulos-del-sistema)
4. [Instalación y Configuración](#-instalación-y-configuración)
5. [Estructura del Proyecto](#-estructura-del-proyecto)
6. [Base de Datos](#-base-de-datos)
7. [Sistema de Autenticación](#-sistema-de-autenticación)
8. [APIs REST](#-apis-rest)
9. [Flujos de Trabajo](#-flujos-de-trabajo)
10. [Variables de Entorno](#-variables-de-entorno)
11. [Deployment](#-deployment)
12. [Testing](#-testing)
13. [Documentación de Código](#-documentación-de-código)
14. [Contribución](#-contribución)
15. [Licencia](#-licencia)

---

## Descripción General

**AGEO** es un sistema web integral desarrollado en Django para la gestión eficiente de trámites ciudadanos y atención a la comunidad. El sistema está compuesto por dos módulos principales que trabajan de forma integrada:

### Características Principales

**Gestión de trámites** de obra pública y desarrollo urbano  
**Atención ciudadana** presencial y en campo  
**Presupuesto participativo** con 5 categorías de proyectos  
**Generación automática** de documentos PDF oficiales  
**Gestión de licitaciones** de obra pública <!-- **Geolocalización** de proyectos y problemas reportados-->  
**APIs REST** para integración con aplicaciones externas  
**Documentación automática** de APIs con Swagger/ReDoc  
**Sistema de autenticación unificado** con roles y permisos  
**Reportes y estadísticas** en tiempo real  

### Tecnologías Utilizadas

| Categoría           | Tecnología                                          |
|---------------------|-----------------------------------------------------|
| **Backend**         | Django 5.0, Django REST Framework 3.16.1            |
| **Base de Datos**   | MySQL 8.0+ con mysqlclient 2.2.7                    |
| **Frontend**        | HTML5, CSS3, JavaScript, Bootstrap 5.25             |
| **PDF Generation**  | WeasyPrint 66.0                                     |
| **APIs**            | DRF 3.16.1, drf-yasg 1.21.11 (Swagger), JWT 5.5.1   |
| **Geolocalización** | ArcGIS Server Local, OpenStreetMap, WSDomicilios    |
| **Autenticación**   | Django Auth + Backend personalizado, Session-based  |
| **Async Tasks**     | Celery 5.5.3, Redis 6.4.0, django-celery-beat 2.8.1 |
| **Servidor**        | Gunicorn 23.0.0, Nginx, Ubuntu Server 22.04         |
| **Cache**           | Redis 6.4.0, django-redis 6.0.0                     |
| **Monitoreo**       | Sentry SDK 2.42.0                                   |
| **Seguridad**       | django-cors-headers 4.9.0, cryptography 46.0.3      |

---

## Arquitectura del Sistema

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    AGEO - Sistema Principal                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │   MÓDULO CMIN        │      │   MÓDULO AGEO        │     │
│  │   (Administrador)    │◄────►│ (Levantamiento de    |     |
|  |                      |      |     necesidades)     │     │
│  └──────────────────────┘      └──────────────────────┘     │
│           │                              │                  │
│           │                              │                  │
│           ▼                              ▼                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Sistema de Autenticación Unificado           │   │
│  │              (portaldu.cmin.models.Users)            │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                              │                  │
│           ▼                              ▼                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Base de Datos (MySQL)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                                     │
         ▼                                     ▼
┌──────────────────┐                 ┌──────────────────┐
│   APIs REST      │                 │   Documentación  │
│/cmin/solicitudes/│                 │   /swagger/      │
│   /ageo/api_sol/ │                 │   /redoc/        │
└──────────────────┘                 └──────────────────┘
```

### Flujo de Datos General

```
Usuario → Login → Validación → Roles → Módulo correspondiente
                                        ├─> CMIN (Módulo de administración)
                                        |        ├─> Creación de usuarios
                                        |        ├─> Asignación de solicitudes
                                        |        ├─> Análisis de seguimiento
                                        |        └─> Administración de solicitudes
                                        └─> AGEO (Trámites en campo)
                                                 ├─> Captura datos
                                                 ├─> Genera folio
                                                 ├─> Crea PDF
                                                 └─> Almacena en BD
```

---

## Módulos del Sistema

### CMIN - Módulo de dministración de AGEO

**Ruta base**: `/cmin/`  
**API**: `/cmin/solicitudes/`

#### Funcionalidades

- **Administración de solicitudes**
  - Asignación de solicitudes
  - Cambios de estado (pendiente, en proceso, completado)
  - Validación de documentos de seguimineto
  - Cierre de solicitudes

- **Gestión de Licitaciones (WIP)**
  - CRUD completo de licitaciones
  - Publicación de convocatorias
  - Administración de fechas límite
  - Seguimiento de participantes

- **Reportes y Estadísticas**
  - Dashboard con métricas en tiempo real (WIP?)
  - Reportes por fecha, tipo, empleado (WIP?)
  - Exportación a Excel/PDF (WIP)
  <!-- Gráficas interactivas (hell nah)-->

- **Sistema de Usuarios**
  - Gestión centralizada de usuarios
  - Roles y permisos granulares
  - Auditoría de accesos
  - Configuración de perfiles

#### Roles en CMIN

| Rol             | Permisos | Descripción |
|-----------------|----------|-------------|
| `Campo`         | Lectura/Escritura trámites | Usuario básico de atención |
| `Delegado`      | Lectura/Escritura + Reportes | Supervisión de operaciones |
| `Administrador` | Acceso total CMIN | Gestión completa del módulo |
| `Superusuario`  | Acceso total sistema | Control total (ambos módulos) |

### AGEO - Gestión de Obra Pública (DesUr)

**Ruta base**: `/ageo/`  
**API**: `/ageo/api_sol/`

#### Funcionalidades

- **Captura de Trámites en Campo**
  - Registro de datos ciudadanos (CURP, teléfono, dirección)
  - Captura de solicitudes con fotografías
  - Geolocalización(?) de problemas / localización de solicitudes
  - Documentos adjuntos múltiples
  - Generación automática de folios

- **Presupuesto Participativo**
  - 5 categorías de proyectos:
    1. **Parques**: Canchas, alumbrado, juegos, techumbres, equipamiento
    2. **Escuelas**: Rehabilitación, construcción, áreas deportivas
    3. **Centros Comunitarios**: Espacios de reunión y eventos
    4. **Infraestructura**: Bardas, banquetas, pavimentación, señalamiento
    5. **Soluciones Pluviales**: Drenaje, canalizaciones, protección
  - Evaluación de instalaciones existentes
  - Generación de propuestas con folio único

- **Generación de Documentos**
  - PDFs oficiales con folio
  - Comprobantes de trámites
  - Documentos de presupuesto participativo
  - Almacenamiento en base de datos

- **Servicios de Geolocalización(?) / Locaclización**
  - Geocodificación (dirección → coordenadas(?))
  - Geocodificación inversa (coordenadas → dirección)(Ya no?)
  - Validación con catastro local
  - Sugerencias de direcciones

#### Códigos de Trámites (DOP)

| Código      | Descripción |
|-------------|-------------|
| `DOP00001`  | Arreglo de calles de terracería |
| `DOP00002`  | Bacheo de calles |
| `DOP00003`  | Limpieza de arroyos al sur |
| `DOP00004`  | Limpieza de rejillas pluviales |
| `DOP00005`  | Pago de licitaciones |
| `DOP00006`  | Rehabilitación de calles |
| `DOP00007`  | Retiro de escombro |
| `DOP00008`  | Solicitud de material caliche/fresado |
| `DOP00009`  | Solicitud de pavimentación |
| `DOP000010` | Reductores de velocidad |
| `DOP000011` | Pintura para señalamientos |
| `DOP000012` | Arreglo de derrumbes de bardas |
| `DOP000013` | Tapiado |

#### Tipos de Proceso (PUO)

| Código | Descripción                          | Formato Folio         |
|--------|--------------------------------------|-----------------------|
| `OFI` | Oficio                               | DOP-OFI-#####-XXXX/YY |
| `CRC` | CRC                                  | DOP-CRC-#####-XXXX/YY |
| `MEC` | Marca el cambio                      | DOP-MEC-#####-XXXX/YY |
| `DLO` | Diputado Local                       | DOP-DLO-#####-XXXX/YY |
| `DFE` | Diputado Federal                     | DOP-DFE-#####-XXXX/YY |
| `REG` | Regidores                            | DOP-REG-#####-XXXX/YY |
| `DEA` | Despacho del Alcalde                 | DOP-DEA-#####-XXXX/YY |
| `EVA` | Evento con el Alcalde                | DOP-EVA-#####-XXXX/YY |
| `PED` | Presencial en Dirección              | DOP-PED-#####-XXXX/YY |
| `VIN` | Vinculación                          | DOP-VIN-#####-XXXX/YY |
| `PPA` | Presupuesto Participativo            | DOP-PPA-#####-XXXX/YY |
| `CPC` | Coordinación Participación Ciudadana | DOP-CPC-#####-XXXX/YY |

---

## Instalación y Configuración

### Requisitos Previos

```bash
# Software requerido
- Python 3.11 o superior
- pip (administrador de paquetes Python)
- Git
- Virtualenv (recomendado)

# Para producción
- Mysql 8+
- Nginx
- Gunicorn
- Redis (para Celery, opcional)
```

### Instalación Paso a Paso

#### 1. Clonar el Repositorio

```bash
git clone https://github.com/ridelyEX/civitas.git
cd civitas
```

#### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Django Settings
SECRET_KEY=tu-clave-secreta-aqui-cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=dirección_host

# Base de Datos (Producción)
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=ageo
# DB_USER=usuario_ageo
# DB_PASSWORD=password_seguro
# DB_HOST=localhost
# DB_PORT=3306

# Email Settings (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=password-de-aplicación

# Celery (opcional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 5. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. Crear Superusuario

```bash
python manage.py createsuperuser
```

#### 7. Recopilar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

#### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Acceder a: `http://localhost:8000`

### Script de Configuración Rápida (Windows)

El proyecto incluye `setup_project.bat` para configuración automática:

```bash
setup_project.bat
```
---
### Configuración en Servidor Linux

El sistema está diseñado para desplegarse en un servidor Ubuntu 22.04 con Nginx y Gunicorn. Se requieren dos archivos de configuración:

#### 1. Configuración de Nginx

Crear archivo en `/etc/nginx/sites-available/civitas`:

```nginx
server {
    listen 80;
    server_name tu-dominio.gob.mx www.tu-dominio.gob.mx;
    
    client_max_body_size 50M;
    
    location /static/ {
        alias /home/usuario/civitas/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
    }
    
    location /media/ {
        alias /home/usuario/civitas/media/;
        expires 7d;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options "nosniff";
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/civitas/civitas.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
    
    # Headers de seguridad
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}

# Habilitar el sitio
# sudo ln -s /etc/nginx/sites-available/civitas /etc/nginx/sites-enabled/
# sudo nginx -t
# sudo systemctl reload nginx
```

### 2. Servicio Systemd

El sistema AGEO utiliza servicios systemd para gestionar los procesos de Celery (worker y beat) que ejecutan tareas asíncronas y programadas. Esta sección explica cómo configurar, activar y monitorear estos servicios en un entorno de producción Ubuntu 22.04.

---

#### Arquitectura de servicios

```
┌─────────────────────────────────────────────────────────────┐
│                    AGEO - Servicios Systemd                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │   Redis Server       │      │   Django/Gunicorn    │     │
│  │   (Broker/Backend)   │      │   (Aplicación Web)   │     │
│  └──────────────────────┘      └──────────────────────┘     │
│           │                              │                  │
│           └──────────────┬───────────────┘                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Celery Worker                          │   │
│  │    (procesa tareas asíncronas en background)         │   │
│  │    Servicio: celery-worker.service                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Celery Beat                            │   │
│  │    (scheduler de tareas periódicas)                  │   │
│  │    Servicio: celery-beat.service                     │   │
│  │    Depende de: celery-worker.service                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
---

# Prerequisitos

## Verificar Redis
sudo systemctl status redis-server

## Si no está instalado:
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
---

### Configuración de servicios

#### 1. Servicio Celery Worker

Este servicio ejecuta las tareas asíncronas (envío de emails, procesamiento de documentos, etc.).

Crear archivo: `/etc/systemd/system/celery-worker.service`

```ini
[Unit]
Description=Celery Worker for AGEO
After=network.target redis-server.service mysql.service
Requires=redis-server.service

[Service]
Type=exec
User=tstopageo
Group=www-data
WorkingDirectory=/home/tstopageo/dev/civitas

Environment="PATH=/home/tstopageo/dev/civitas/venv/bin"
Environment="PYTHONPATH=/home/tstopageo/dev/civitas"

ExecStart=/home/tstopageo/dev/civitas/venv/bin/celery -A civitas worker \
    --loglevel=info \
    --logfile=/home/tstopageo/dev/civitas/logs/celery-worker.log \
    --pidfile=/run/civitas/celery-worker.pid \
    --concurrency=4 \
    --max-tasks-per-child=1000

Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Parámetros importantes:
User=tstopageo: Usuario que ejecuta el servicio (cambiar según tu sistema)
WorkingDirectory: Ruta absoluta al proyecto Django
--concurrency=4: Número de workers (ajustar según CPU)
--max-tasks-per-child=1000: Reinicia workers cada 1000 tareas (previene memory leaks)

#### 2. Servicio Celery Beat
Este servicio programa tareas periódicas (reportes automáticos, limpieza de logs, backups).
Crear archivo: /etc/systemd/system/celery-beat.service

```ini
[Unit]
Description=Celery Beat for AGEO
After=network.target redis-server.service mysql.service celery-worker.service
Requires=redis-server.service

[Service]
Type=exec
User=tstopageo
Group=www-data
WorkingDirectory=/home/tstopageo/dev/civitas

Environment="PATH=/home/tstopageo/dev/civitas/venv/bin"
Environment="PYTHONPATH=/home/tstopageo/dev/civitas"

ExecStart=/home/tstopageo/dev/civitas/venv/bin/celery -A civitas beat \
    --logLevel=info \
    --logfile=/home/tstopageo/dev/civitas/logs/celery-beat.log \
    --pidfile=/run/civitas/celery-beat.pid \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

```

Nota importante: celery-beat.service requiere que celery-worker.service esté activo. Si el worker falla, beat también se detendrá (Requires=celery-worker.service).

---

Crear archivo en `/etc/systemd/system/civitas.service`:

```ini
[Unit]
Description=CIVITAS Django Application
After=network.target mysql.service
Requires=mysql.service

[Service]
User=usuario
Group=www-data
WorkingDirectory=/home/usuario/civitas
Environment="PATH=/home/usuario/civitas/venv/bin"

# Usar archivo de configuración de Gunicorn
ExecStart=/home/usuario/civitas/venv/bin/gunicorn \
    --config /home/usuario/civitas/gunicorn.conf.py \
    civitas.wsgi:application

# Reinicio automático
Restart=on-failure
RestartSec=5s

# Límites de recursos
LimitNOFILE=65536

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Comandos de gestión:
# sudo systemctl daemon-reload
# sudo systemctl enable civitas
# sudo systemctl start civitas
# sudo systemctl status civitas
```

#### 3. Configuración de Gunicorn

El proyecto incluye `gunicorn.conf.py` con la configuración recomendada:

```python
bind = "unix:/run/civitas/civitas.sock"
workers = 9
threads = 2
timeout = 120
worker_class = "gthread"
```

**Nota**: Crear el directorio para el socket antes de iniciar:

---

```bash
sudo mkdir -p /run/civitas
sudo chown usuario:www-data /run/civitas
```

### Instalación y activación

#### 1. Crear directorios

```bash
# Directorio de logs
sudo mkdir -p /home/tstopageo/dev/civitas/logs
sudo chown -R tstopageo:www-data /home/tstopageo/dev/civitas/logs

# Directorio para PID files (se crea automáticamente por RuntimeDirectory)
# Pero aseguramos permisos del padre
sudo mkdir -p /run/civitas
sudo chown tstopageo:www-data /run/civitas
```

#### 2. Copiar archivos de servicio

```bash
# Copiar archivos (o crearlos con nano/vim)
sudo cp civitas.service /etc/systemd/system/
sudo cp nginx.service /etc/systemd/system/
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/

# O crear directamente
sudo nano /etc/systemd/system/civitas.service
sudo nano /etc/systemd/system/nginx.service
sudo nano /etc/systemd/system/celery-worker.service
sudo nano /etc/systemd/system/celery-beat.service
```

#### 3. Verificar sintaxis y recargar systemd

```bash
# Verificar sintaxis de archivos
sudo systemd-analyze verify /etc/systemd/system/celery-worker.service
sudo systemd-analyze verify /etc/systemd/system/celery-beat.service

# Recargar configuración de systemd
sudo systemctl daemon-reload
```

#### 4. Habilitar servicios (auto-inicio en boot)

```bash
# Habilitar gunicor
sudo systemctl enable civitas.service

# Habilitar nginx
sudo systemctl enable nginx.service

# Habilitar worker
sudo systemctl enable celery-worker.service

# Habilitar beat (automáticamente habilita worker por dependencia)
sudo systemctl enable celery-beat.service

# Verificar que están habilitados
systemctl is-enabled civitas
systemctl is-enabled nginx
systemctl is-enabled celery-worker
systemctl is-enabled celery-beat
```

#### 5. Iniciar servcios

```bash 
# IMPORTANTE: Iniciar en orden
# 1. Iniciar gunicorn
sudo systemctl start civitas.service

# 2. Iniciar el servidor nginx
sudo systemctl start nginx.service

# 3. Esperar 5 segundos y verificar el servidor
sleep 5
sudo systemctl status nginx.service

# 4. Si el servidor está activo, iniciar worker
sleep 5
sudo systemctl start celery-worker.service

# 5. Esperar 5 segundos y verificar worker
sleep 5
sudo systemctl status celery-worker.service

# 6. Si worker está activo, iniciar beat
sudo systemctl start celery-beat.service

# 7. Verificar beat
sudo systemctl status celery-beat.service
```

### Comandos de gestión

---

```bash
# Iniciar servicios
sudo systemctl start civitas
sudo systemctl start nginx
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# Detener servicios
sudo systemctl stop civitas        # Detener gunicor
sudo systemctl stop nginx          # Después el servidor nginx
sudo systemctl stop celery-beat    # Luego beat 
sudo systemctl stop celery-worker  # Finalmente worker

# Reiniciar servicios
sudo systemctl restart civitas
sudo systemctl restart nginx
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

# Recargar configuración sin detener
sudo systemctl reload celery-worker  # Envía señal HUP
```

### Comandos de estado

```bash
# Ver estado general
systemctl status civitas
systemctl status nginx
systemctl status celery-worker
systemctl status celery-beat

# Estado con más detalles
systemctl status celery-worker -l --no-pager

# Ver si están activos
systemctl is-active civitas
systemctl is-active nginx
systemctl is-active celery-worker
systemctl is-active celery-beat

# Ver si falló
systemctl is-failed celery-worker
systemctl is-failed celery-beat
```

### Comandos de Logs

```bash
# Ver logs en tiempo real
sudo journalctl -u civitas -f
sudo journalctl -u nginx -f
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f

# Ver últimas 50 líneas
sudo journalctl -u civitas -n 50
sudo journalctl -u nginx -n 50
sudo journalctl -u celery-worker -n 50
sudo journalctl -u celery-beat -n 50

# Ver logs desde hace 1 hora
sudo journalctl -u celery-worker --since "1 hour ago"

# Ver logs con prioridad (error y crítico)
sudo journalctl -u celery-worker -p err

# Ver logs de celery- worker/beat
sudo journalctl -u celery-worker -u celery-beat -f
```

### Actualización de servicios

```bash
# 1. Detener servicios
sudo systemctl stop civitas
sudo systemctl stop nginx
sudo systemctl stop celery-beat
sudo systemctl stop celery-worker

# 2. Actualizar código
cd /home/tstopageo/dev/civitas
git pull origin main

# 3. Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Recargar systemd si se modificaron .service
sudo systemctl daemon-reload

# 6. Reiniciar servicios
sudo systemctl start civitas
sleep 5
sudo systemctl start nginx
sleep 5
sudo systemctl start celery-worker
sleep 5
sudo systemctl start celery-beat

# 7. Verificar
sudo systemctl status celery-worker
sudo systemctl status celery-beat
sudo systemctl status civitas
sudo systemctl status nginx
```
---

# Mantenimiento

### Rotación de Logs

Crear archivo `/etc/logrotate.d/celery`
/home/tstopageo/dev/civitas/logs/celery-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 tstopageo www-data
    sharedscripts
    postrotate
        systemctl reload celery-worker > /dev/null 2>&1 || true
        systemctl reload celery-beat > /dev/null 2>&1 || true
    endscript
}

Aplicar:
```bash
sudo logrotate -f /etc/logrotate.d/celery
```

Limpieza manual de logs
```bash
# Comprimir logs antiguos
find /home/tstopageo/dev/civitas/logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# Eliminar logs >30 días
find /home/tstopageo/dev/civitas/logs/ -name "*.log.gz" -mtime +30 -delete
```



## Estructura del Proyecto

```
civitas/
├── civitas/                    # Configuración principal del proyecto
│   ├── __init__.py
│   ├── settings.py            # Configuraciones generales
│   ├── urls.py                # URLs principales
│   ├── wsgi.py                # WSGI para deployment
│   └── asgi.py                # ASGI para async
│
├── portaldu/                   # Paquete de aplicaciones
│   ├── cmin/                   # Módulo CMIN
│   │   ├── models.py          # Modelos: Users, Licitaciones, LoginDate, etc.
│   │   ├── views.py           # Vistas principales
│   │   ├── api_views.py       # ViewSets de API REST
│   │   ├── serializers.py     # Serializers DRF
│   │   ├── forms.py           # Formularios Django
│   │   ├── urls.py            # URLs del módulo
│   │   ├── api_urls.py        # URLs de API
│   │   ├── admin.py           # Configuración admin
│   │   └── templates/         # Templates HTML
│   │
│   └── desUr/                  # Módulo AGEO
│       ├── models.py          # Modelos: data, soli, Files, PpGeneral, etc.
│       ├── views.py           # 70+ vistas
│       ├── api_views.py       # ViewSets API
│       ├── serializers.py     # 5 Serializers
│       ├── forms.py           # 10 Formularios
│       ├── urls.py            # 35+ URLs
│       ├── api_urls.py        # API REST
│       ├── auth.py            # Autenticación
│       ├── services.py        # LocalGISService
|       ├── WsConfig.py        # WsConfig
|       ├── WSDServices.py     # WsDomicilios
│       ├── admin.py           # Configuración admin
│       └── templates/         # Templates HTML
│
├── media/                      # Archivos subidos por usuarios
│   ├── documents/             # Documentos adjuntos
│   ├── fotos/                 # Fotos de problemas
│   ├── user_photos/           # Fotos de perfil
│   └── pp_solicitudes/        # Documentos de presupuesto participativo
│
├── staticfiles/                # Archivos estáticos recopilados
│   ├── admin/                 # Assets de Django Admin
│   ├── cminStyles/            # CSS de CMIN
│   ├── cminScripts/           # JS de CMIN
│   ├── styles/                # CSS de AGEO
│   └── sripts/                # JS de AGEO
│
├── logs/                       # Logs del sistema
│   └── civitas.log            # Log principal
│
├── db.sqlite3                  # Base de datos SQLite (No funcional)
├── manage.py                   # Script de gestión Django
├── requirements.txt            # Dependencias Python
├── setup_project.bat           # Script de configuración (Windows)
├── docker-compose.yml          # Configuración Docker
├── Dockerfile                  # Imagen Docker
└── README.md                   # Esta documentación
```

---

## Base de Datos

### Modelos Principales

#### CMIN

```python
# portaldu/cmin/models.py

class Users(AbstractBaseUser):
    """Modelo unificado de usuarios del sistema"""
    user_id = AutoField(primary_key=True)
    username = CharField(unique=True)
    email = EmailField(unique=True)
    first_name = CharField()
    last_name = CharField()
    rol = CharField()  # Empleado, Supervisor, Administrador, Superusuario
    bday = DateField()
    foto = ImageField()
    module_cmin = BooleanField(default=False)
    module_desur = BooleanField(default=False)
    
class Licitaciones:
    """Licitaciones de obra pública"""
    licitacion_ID = AutoField(primary_key=True)
    no_licitacion = CharField()
    desc_licitacion = TextField()
    fecha_limite = DateField()
    monto_estimado = DecimalField()
    activa = BooleanField(default=True)

class LoginDate:
    """Registro de accesos al sistema"""
    date = DateTimeField(auto_now_add=True)
    user = ForeignKey(Users)
```

#### AGEO (DesUr)

```python
# portaldu/desUr/models.py

class Uuid:
    """Identificadores de sesión de trabajo"""
    prime = AutoField(primary_key=True)
    uuid = UUIDField(default=uuid.uuid4, unique=True)

class data:
    """Datos de ciudadanos"""
    data_ID = AutoField(primary_key=True)
    fuuid = ForeignKey(Uuid)
    nombre = CharField()
    pApe = CharField()  # Apellido paterno
    mApe = CharField()  # Apellido materno
    bDay = DateField()
    tel = CharField()
    curp = CharField(unique=True)
    sexo = CharField()
    dirr = CharField()
    asunto = CharField()
    etnia = CharField()
    disc = CharField()
    vul = CharField()

class soli:
    """Solicitudes de trámites"""
    soli_ID = AutoField(primary_key=True)
    data_ID = ForeignKey(data)
    dirr = CharField()
    info = TextField()
    descc = TextField()
    foto = ImageField()
    puo = CharField()
    folio = CharField(unique=True)
    fecha = DateTimeField(auto_now_add=True)
    processed_by = ForeignKey(Users)

class Files:
    """Documentos finales generados"""
    fDoc_ID = AutoField(primary_key=True)
    nomDoc = CharField()
    finalDoc = FileField()
    fuuid = ForeignKey(Uuid)
    soli_FK = ForeignKey(soli)
```

### Diagrama de Relaciones

```
Users (CMIN)
    ↓ (1:N)
    ├── LoginDate (registros de acceso)
    └── soli (trámites procesados)

Uuid (sesión)
    ↓ (1:1)
    ├── data (ciudadano)
    ├── SubirDocs (documentos temporales)
    ├── Files (documentos finales)
    └── PpGeneral (propuesta PP)
            ↓ (1:1)
            ├── PpParque
            ├── PpEscuela
            ├── PpCS
            ├── PpInfraestructura
            └── PpPluvial

data (ciudadano)
    ↓ (1:N)
    └── soli (solicitudes)
            ↓ (1:N)
            └── Files (documentos)
```

---

## Sistema de Autenticación

### Autenticación Unificada

El sistema utiliza un **modelo único de usuarios** (`portaldu.cmin.models.Users`) compartido entre ambos módulos.

#### Backend de Autenticación

```python
# portaldu/desUr/auth.py

class CivitasAuthBackend(ModelBackend):
    """Backend de autenticación unificado"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Permite login con username o email"""
        try:
            user = Users.objects.get(
                Q(username=username) | Q(email=username)
            )
            if user.check_password(password):
                return user
        except Users.DoesNotExist:
            return None
```

#### Decoradores de Permisos

```python
# Decorador para CMIN
@login_required
@cmin_access_required
def vista_cmin(request):
    # Solo usuarios con module_cmin=True
    pass

# Decorador para AGEO
@login_required
@desur_access_required
def vista_ageo(request):
    # Solo usuarios con module_desur=True
    pass
```

### Flujo de Login

```
1. Usuario accede a /auth/login/
2. Ingresa username y password
3. CivitasAuthBackend valida credenciales
4. Sistema verifica roles (module_cmin, module_desur)
5. Redirige según permisos:
   - CMIN → /cmin/
   - AGEO → /ageo/
   - Ambos → Menú de selección
```

---

## APIs REST

### Documentación Automática

- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **Schema JSON**: `http://localhost:8000/swagger.json`

### API AGEO (DesUr)

Base URL: `/api/ageo/`

#### Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/uuid/` | Crear UUID de sesión |
| `POST` | `/data/` | Enviar datos de ciudadano |
| `POST` | `/soli/` | Crear solicitud de trámite |
| `POST` | `/files/` | Subir documento final |
| `GET` | `/ciudadanos/` | Listar ciudadanos (paginado) |
| `POST` | `/ciudadanos/` | Crear ciudadano |
| `GET` | `/ciudadanos/{id}/` | Detalle de ciudadano |
| `PUT` | `/ciudadanos/{id}/` | Actualizar ciudadano |
| `DELETE` | `/ciudadanos/{id}/` | Eliminar ciudadano |

#### Ejemplo: Crear Trámite Completo

```bash
# 1. Crear UUID de sesión
curl -X POST http://localhost:8000/api/ageo/uuid/ \
  -H "Content-Type: application/json" \
  -d '{}'

# Response:
{
  "status": "success",
  "data": {
    "prime": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
  }
}

# 2. Enviar datos del ciudadano
curl -X POST http://localhost:8000/api/ageo/data/ \
  -H "Content-Type: application/json" \
  -d '{
    "fuuid": 123,
    "nombre": "Juan Carlos",
    "pApe": "Pérez",
    "mApe": "García",
    "bDay": "1990-01-15",
    "tel": "6441234567",
    "curp": "PEGJ900115HCHRXN09",
    "sexo": "H",
    "dirr": "Calle Ejemplo 123, Colonia Centro",
    "asunto": "DOP00002"
  }'

# 3. Crear solicitud
curl -X POST http://localhost:8000/api/ageo/soli/ \
  -H "Content-Type: application/json" \
  -d '{
    "data_ID": 456,
    "dirr": "Calle Principal esquina con Secundaria",
    "info": "Bache grande en la esquina",
    "descc": "Bache de aproximadamente 50cm de diámetro",
    "puo": "OFI"
  }'
```

---

## Reportes y Estadísticas

El sistema AGEO incluye un completo módulo de reportes y estadísticas para análisis de datos, monitoreo de operaciones y toma de decisiones. Todos los reportes están disponibles para usuarios con rol de **Administrador** o **Delegado**.

### Tipos de Reportes Disponibles

#### 1. Reporte Completo en Excel

**Ruta**: `/cmin/importar/`  
**Método**: POST  
**Permisos**: Administrador, Delegado

Genera un archivo Excel multi-hoja con datos completos del sistema.

**Hojas incluidas**:

1. **Ciudadanos**
   - ID del ciudadano
   - UUID de sesión
   - Nombre completo (nombre, apellido paterno, apellido materno)
   - Fecha de nacimiento
   - Teléfono
   - CURP
   - Género
   - Asunto (código DOP)
   - Dirección completa
   - Discapacidad
   - Etnia
   - Grupo vulnerable

2. **Solicitudes**
   - ID de la solicitud
   - UUID del ciudadano
   - Procesado por (usuario)
   - Dirección del problema
   - Descripción
   - Fecha de creación
   - Información adicional
   - P.U.O (Tipo de proceso)
   - Folio

3. **Solicitudes Pendientes**
   - ID de solicitud pendiente
   - Nombre de la solicitud
   - Fecha de solicitud
   - Destinatario

4. **Solicitudes Enviadas**
   - ID de solicitud enviada
   - Usuario que envió
   - Documento asociado
   - Solicitud pendiente asociada
   - Usuario asignado
   - Folio
   - Categoría
   - Prioridad (Alta/Media/Baja)
   - Estado (pendiente/en_proceso/completado)
   - Fecha de envío

**Características del reporte**:
- Selección de hojas a incluir mediante checkboxes
- Selección de campos específicos por hoja
- Formato automático de columnas (ancho optimizado)
- Formato de fechas en formato DD/MM/YYYY
- Headers con formato visual (fondo azul, texto blanco, centrado)
- Cache de archivos estáticos de 30 días
- Generación con pandas y xlsxwriter

**Ejemplo de uso**:
```python
# La vista procesa formulario POST con campos seleccionados
# y genera archivo Excel con nombre: reporte_completo.xlsx
```

#### 2. Panel de Seguimiento

**Ruta**: `/cmin/seguimiento/`  
**Método**: GET  
**Permisos**: Administrador, Delegado

Panel interactivo para monitoreo y seguimiento de solicitudes procesadas.

**Estadísticas disponibles**:
- **Total de solicitudes**: Contador general de solicitudes en el sistema
- **Cerradas**: Solicitudes que han sido completadas y cerradas formalmente
- **Activas**: Solicitudes aún en proceso (sin cierre)
- **Con seguimiento**: Solicitudes que tienen al menos un registro de seguimiento

**Filtros disponibles**:
- **Búsqueda por texto**: 
  - Nombre de solicitud
  - Folio
  - Destinatario
- **Estado**:
  - Cerrada
  - Activa
  - Con seguimiento
  - Sin seguimiento
- **Usuario**: Filtrar por usuario que envió la solicitud
- **Prioridad**: Alta, Media, Baja
- **Rango de fechas**: Desde - Hasta

**Funcionalidades adicionales**:
- Ver historial completo de seguimiento por solicitud
- Agregar nuevos registros de seguimiento
- Subir documentos de evidencia
- Cerrar solicitudes (con o sin seguimiento previo)
- Ver documentos asociados
- Estadísticas en tiempo real

#### 3. Bandeja de Entrada Personal

**Ruta**: `/cmin/bandeja/`  
**Método**: GET  
**Permisos**: Todos los usuarios autenticados

Panel personalizado que muestra solo las solicitudes asignadas al usuario logueado.

**Estadísticas personales**:
- **Total**: Todas las solicitudes asignadas al usuario
- **Pendientes**: Solicitudes en espera de atención
- **En proceso**: Solicitudes siendo trabajadas activamente
- **Completadas**: Solicitudes finalizadas por el usuario

**Filtros disponibles**:
- **Estado**: pendiente, en_proceso, completado
- **Prioridad**: Alta, Media, Baja

**Funcionalidades**:
- Cambio de estado de solicitudes vía AJAX
- Visualización de evidencias agrupadas por solicitud
- Actualización en tiempo real sin recargar página
- Historial de seguimiento asociado
- Notificaciones automáticas al cambiar estados

**Flujo de actualización de estado**:
```
1. Usuario selecciona solicitud
2. Cambia estado (pendiente → en_proceso → completado)
3. Sistema registra cambio automáticamente
4. Genera notificación al usuario asignador
5. Actualiza estadísticas en tiempo real
```

#### 4. Consulta de Encuestas Móviles

**Ruta**: `/cmin/encuestas/`  
**Método**: GET  
**Permisos**: Administrador, Delegado

Sistema completo de análisis de encuestas recibidas desde aplicaciones móviles.

**Estadísticas generales**:
- **Total de encuestas**: Contador completo de encuestas recibidas
- **Sincronizadas**: Encuestas procesadas correctamente
- **No sincronizadas**: Encuestas pendientes de sincronización
- **Completadas**: Encuestas con todas las respuestas
- **Incompletas**: Encuestas parciales
- **Por género**: Distribución de encuestas por género del encuestado

**Filtros avanzados**:
- **Búsqueda por texto**:
  - Nombre de escuela
  - Colonia
  - UUID de encuesta
- **Escuela**: Selección de escuela específica
- **Colonia**: Filtro por colonia
- **Rol social**: Estudiante, padre, maestro, etc.
- **Género**: Masculino, femenino, otro
- **Tipo de proyecto**: Categoría del proyecto evaluado
- **Rango de fechas**: Fecha desde - Fecha hasta
- **Estado de sincronización**: Sincronizada (1) o No sincronizada (0)
- **Estado de completitud**: Completada (1) o Incompleta (0)

**Datos visualizados por encuesta**:
- UUID único
- Fecha de respuesta
- Escuela
- Colonia
- Rol social del encuestado
- Género
- Nivel escolar
- Grado escolar
- Comunidad indígena (si aplica)
- Grupo vulnerable (si aplica)
- Tipo de proyecto
- 17 preguntas con respuestas (numéricas y texto)
- Estado de sincronización
- Estado de completitud
- Foto asociada (URL)
- Timestamps (created_at, updated_at)

**Exportación de datos**:
- Exportación a Excel con filtros aplicados
- Exportación de encuestas individuales
- Exportación de estadísticas agregadas

#### 5. Panel de Tablas (Solicitudes de DesUr)

**Ruta**: `/cmin/tables/`  
**Método**: GET  
**Permisos**: Administrador, Delegado

Panel principal para gestión de documentos recibidos desde el módulo AGEO.

**Listados disponibles**:

**a) Documentos de DesUr (Files)**
- Nombre del documento
- Folio de solicitud asociada
- UUID de sesión
- Fecha de creación
- Acciones: Ver PDF, Guardar como pendiente

**b) Solicitudes Pendientes**
- ID de solicitud pendiente
- Nombre de la solicitud
- Fecha de solicitud
- Destinatario
- Documento asociado
- Acciones: Procesar y enviar

**c) Solicitudes Enviadas**
- ID de solicitud enviada
- Nombre de la solicitud
- Usuario que envió
- Folio
- Categoría
- Prioridad
- Estado
- Usuario asignado
- Fecha de envío
- Acciones: Ver seguimiento

**Funcionalidades**:
- Conversión de documentos a solicitudes pendientes
- Asignación de destinatarios
- Procesamiento y envío por email
- Asignación de usuario responsable
- Definición de prioridad
- Cambio de categoría

#### 6. Reportes Periódicos Automáticos (Celery)

**Tarea**: `generate_reports()`  
**Frecuencia**: Configurable vía Celery Beat  
**Ejecución**: Asíncrona

Tarea programada que genera reportes automáticos del sistema.

**Métricas incluidas**:
```python
{
    "total_solicitudes": int,      # Total de solicitudes en BD
    "solicitudes_hoy": int,         # Solicitudes creadas hoy
    "total_ciudadanos": int,        # Total de ciudadanos registrados
    "fecha_reporte": str            # ISO 8601 timestamp
}
```

**Almacenamiento**:
- Resultados guardados en Celery Results (Redis o DB)
- Logs en archivo `logs/civitas.log`
- Disponible para consulta vía API de Celery

### Acceso a Reportes según Rol

| Reporte | Administrador | Delegado | Campo |
|---------|--------------|----------|-------|
| Reporte Excel Completo | ✓ | ✓ | ✗ |
| Panel de Seguimiento | ✓ | ✓ | ✗ |
| Bandeja de Entrada | ✓ | ✓ | ✓ |
| Consulta de Encuestas | ✓ | ✓ | ✗ |
| Panel de Tablas | ✓ | ✓ | ✗ |
| Reportes Automáticos | ✓ (configuración) | ✗ | ✗ |

### Formatos de Exportación

**Excel (.xlsx)**:
- Reporte completo multi-hoja
- Formato automático de columnas
- Headers personalizados
- Fechas formateadas
- Compatible con Excel 2010+

**PDF (vía navegador)**:
- Documentos individuales de solicitudes
- Comprobantes de trámites
- PDFs de presupuesto participativo
- Visualización inline o descarga

### Tecnologías Utilizadas

- **pandas 2.3.3**: Procesamiento de datos y DataFrames
- **xlsxwriter 3.2.9**: Generación de archivos Excel con formato
- **ExcelManager (utils)**: Clase personalizada para gestión de Excel
  - Auto-ajuste de columnas
  - Formato de fechas automático
  - Headers con estilo
  - Manejo de errores

### Ejemplo de Uso: Generar Reporte Excel

```html
<!-- Formulario en template -->
<form method="POST" action="{% url 'importar_excel' %}">
    {% csrf_token %}
    
    <!-- Seleccionar hojas -->
    <input type="checkbox" name="incluir_ciudadanos" checked>
    <label>Incluir Ciudadanos</label>
    
    <input type="checkbox" name="incluir_solicitudes" checked>
    <label>Incluir Solicitudes</label>
    
    <!-- Seleccionar campos específicos -->
    <select name="campos_ciudadanos" multiple>
        <option value="data_ID">ID</option>
        <option value="nombre">Nombre</option>
        <option value="curp">CURP</option>
        <!-- ... más campos -->
    </select>
    
    <button type="submit">Generar Reporte</button>
</form>
```

```python
# Procesamiento en backend (views.py)
def get_excel(request):
    # Configuración de modelos y campos
    modelos = [...]
    
    # Generar Excel con pandas
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        manager.create_formats(writer.book)
        
        for config in modelos:
            if request.POST.get(f'incluir_{config["key"]}'):
                # Procesar datos y crear hoja
                manager.process_sheet(df, config['nombre'], writer)
    
    return response  # Descarga automática
```

### Estadísticas en Tiempo Real

Todos los paneles de reportes incluyen estadísticas calculadas dinámicamente:

```python
# Ejemplo: Estadísticas de seguimiento
total_solicitudes = SolicitudesEnviadas.objects.count()
cerradas = SolicitudesEnviadas.objects.filter(close__isnull=False).count()
activas = total_solicitudes - cerradas
con_seguimiento = SolicitudesEnviadas.objects.filter(
    seguimiento__isnull=False
).distinct().count()
```

### Reportes PDF Generados por DesUr/AGEO

El módulo DesUr genera documentos PDF oficiales para todos los trámites capturados en campo. Estos documentos son generados usando **WeasyPrint 66.0** que convierte plantillas HTML con CSS a PDFs de alta calidad.

#### 1. PDF de Trámite General (Obra Pública)

**Ruta de generación**: `/ageo/nada/`  
**Ruta de guardado**: `/ageo/save/`  
**Vista**: `document(request)`  
**Template**: `documet/document.html`  
**Formato**: Tamaño Carta (Letter), márgenes 2.5cm

**Contenido del documento**:

**Encabezado**:
- Logo del Municipio de Chihuahua (icono oficial)
- Título: "Dirección de Obras Públicas" (color azul #2974b1, tamaño 2rem)
- Línea divisoria azul (#77C9FF)

**Sección 1: Asunto**
- Título del trámite con código DOP completo
- Ejemplos:
  - "Arreglo de calles de terracería - DOP00001"
  - "Bacheo de calles - DOP00002"
  - "Limpieza de arroyos al sur de la ciudad - DOP00003"
  - ... (hasta DOP00013)

**Sección 2: Datos del Titular o Interesado**
- **Folio generado**: Formato DOP-{PUO}-#####-XXXX/YY (esquina superior derecha)
- **Fecha de creación**: Timestamp de la solicitud
- **Tabla con información personal**:
  - Nombre completo
  - Apellido paterno
  - Apellido materno
  - Fecha de nacimiento
  - Teléfono (formato E164 +52XXXXXXXXXX)
  - CURP (18 caracteres)
  - Sexo
  - Dirección completa
  - Discapacidad (si aplica)
  - Etnia (si aplica)
  - Grupo vulnerable (o "No pertenece a un grupo vulnerable")

**Sección 3: Detalles de la Solicitud**
- **Dirección del problema**: Ubicación específica del reporte
- **Descripción**: Detalle del problema o necesidad
- **Información adicional**: Datos complementarios
- **Fotografía del problema**: Imagen embebida en el PDF (si fue capturada)
- **Origen del trámite (PUO)**: Texto descriptivo del proceso
  - Ejemplos: "Oficio", "CRC", "Marca el cambio", "Diputado Local", etc.

**Sección 4: Documentos Adjuntos**
- Lista de documentos temporales subidos durante el trámite
- Nombre de cada documento
- Descripción de cada archivo
- Referencia a archivos almacenados en `media/documents/`

**Características técnicas**:
- **Tamaño de página**: Letter (8.5" x 11")
- **Márgenes**: 2.5cm en todos los lados
- **Numeración**: Contador de páginas en esquina inferior derecha
- **Fuente**: Franklin Gothic Medium, Arial Narrow, Arial (fallback: sans-serif)
- **Colores corporativos**: 
  - Azul primario: #2974b1
  - Azul claro: #77C9FF
  - Fondo de tablas: rgba(187, 255, 241, 0.411)
- **Bootstrap 5.3.6**: Estilos de tablas striped

**Proceso de generación**:
```python
# 1. Obtener datos del ciudadano y solicitud
datos = get_object_or_404(data, fuuid__uuid=uuid)
solicitud = soli.objects.filter(data_ID=datos).latest('fecha')

# 2. Generar o recuperar folio
if solicitud and solicitud.folio:
    folio = solicitud.folio
else:
    puo_txt, folio = gen_folio(uuid_obj, puo)

# 3. Preparar contexto
context = {
    "asunto": asunto_descripcion,
    "datos": {...},  # Info del ciudadano
    "soli": {...},   # Info de la solicitud
    "puo": puo_txt,
    "documentos": SubirDocs.objects.filter(fuuid__uuid=uuid),
    "folio": folio
}

# 4. Renderizar HTML y convertir a PDF
html = render_to_string("documet/document.html", context)
pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/'))
final_pdf = pdf_out.write_pdf()

# 5. Servir PDF inline en navegador
response = HttpResponse(final_pdf, content_type="application/pdf")
response["Content-Disposition"] = "inline; filename=información_general.pdf"
```

**Nombre de archivo al guardar**: `VS_{código_asunto}_{nombre}_{apellido}.pdf`  
**Ubicación en BD**: Modelo `Files`, campo `finalDoc`  
**Ubicación física**: `media/documents/`

#### 2. PDF de Pago de Licitación (DOP00005)

**Ruta**: `/ageo/document2/`  
**Vista**: `document2(request)`  
**Template**: `documet/document2.html`  
**Uso específico**: Comprobante de pago para participación en licitaciones

**Contenido específico**:

**Sección 1: Encabezado**
- Similar al documento general
- Logo y título de Dirección de Obras Públicas

**Sección 2: Titular o Interesado**
- Datos personales completos del ciudadano (mismo formato que documento general)
- Sin campos de discapacidad, etnia o grupo vulnerable

**Sección 3: Datos del Pago**
- **Fecha del pago**: Timestamp de registro
- **Forma de pago (PFM)**: Método utilizado
  - Ejemplos: Efectivo, Transferencia, Tarjeta, Cheque

**Características específicas**:
- Documento más corto (solo 2 secciones principales)
- Enfocado en comprobante de pago
- No incluye fotografías ni documentos adjuntos
- No incluye descripción de problema

**Proceso de generación**:
```python
# 1. Obtener datos del pago
datos = get_object_or_404(data, fuuid__uuid=uuid)
pago = get_object_or_404(Pagos, data_ID=datos)

# 2. Preparar contexto específico de pago
context = {
    "asunto": "Pago de costo de participación en licitaciones - DOP00005",
    "datos": {...},
    "pago": {
        "fecha": pago.fecha,
        "pfm": pago.pfm  # Forma de pago
    }
}

# 3. Generar PDF
html = render_to_string("documet/document2.html", context)
# ... resto del proceso igual
```

#### 3. PDF de Presupuesto Participativo

**Ruta**: `/ageo/pp/document`  
**Vista**: `pp_document(request)`  
**Template**: `documet/pp_document.html`  
**Categorías**: 5 tipos de proyectos con formularios específicos

**Contenido base (todas las categorías)**:

**Encabezado**:
- Logo municipal
- Título: "Dirección de Obras Públicas"
- Título de categoría: "Presupuesto Participativo - {Categoría}"

**Sección 1: Datos del Promovente**
- Nombre del promovente
- Teléfono de contacto (formato E164)
- Dirección del proyecto
  - Calle
  - Colonia
  - Código postal
- Descripción del proyecto
- Fecha de propuesta
- Folio generado: **DOP-CPP-#####-XXXX/YY**

**Sección 2: Evaluación de Instalaciones Existentes**

Tabla con estado de instalaciones básicas del proyecto:
- **CFE** (Instalación eléctrica)
- **Agua** (Sistema de agua potable)
- **Drenaje** (Sistema de drenaje)
- **Impermeabilización**
- **Climas** (Aires acondicionados/calefacción)
- **Alumbrado** (Alumbrado público)

**Estados posibles** (con badges de color):
- **Bueno** (verde #28a745)
- **Regular** (amarillo #ffc107)
- **Malo** (rojo #dc3545)
- **No existe** (gris)

**Sección 3: Propuesta Específica por Categoría**

**a) Categoría: Parques**
- **Canchas deportivas**:
  - Fútbol rápido
  - Fútbol soccer
  - Fútbol 7x7
  - Béisbol
  - Softbol
  - Usos múltiples
  - Otro (especificar)
  
- **Alumbrado**:
  - Rehabilitación de alumbrado existente
  - Alumbrado nuevo
  
- **Juegos**:
  - Dog park (área canina)
  - Juegos infantiles
  - Ejercitadores
  - Otro tipo
  
- **Techumbres**:
  - Domo
  - Kiosko
  
- **Equipamiento**:
  - Botes de basura
  - Bancas
  - Andadores
  - Rampas

**b) Categoría: Escuelas**
- **Nombre de la escuela**
- **Rehabilitación**:
  - Baños
  - Salones
  - Instalación eléctrica
  - Gimnasio
  - Otro tipo
  
- **Construcción nueva**:
  - Domo
  - Aula
  
- **Canchas deportivas**:
  - Fútbol rápido
  - Fútbol 7x7
  - Usos múltiples

**c) Categoría: Centros Comunitarios**
- **Rehabilitación**:
  - Baños
  - Salones
  - Instalación eléctrica
  - Gimnasio
  
- **Construcción nueva**:
  - Salón
  - Domo
  - Otro tipo

**d) Categoría: Infraestructura**
- **Obra civil**:
  - Barda perimetral
  - Banquetas
  - Muro de contención
  - Intervención en camellón
  - Crucero seguro/cruce peatonal
  - Ordenamiento vehicular
  - Escalinatas/rampas
  - Mejoramiento de imagen vehicular
  - Paso peatonal
  - Bayoneta/retorno
  - Pasos pompeyanos/reductores
  - Puente vehicular
  
- **Pavimentación**:
  - Asfalto
  - Concreto hidráulico
  - Rehabilitación
  
- **Señalamiento vial**:
  - Pintura
  - Señales verticales

**e) Categoría: Soluciones Pluviales**
- Muro de contención
- Canalización de arroyo
- Puente peatonal sobre arroyo
- Construcción de vado
- Puente vehicular
- Solución de desalojo pluvial
- Rejillas pluviales
- Lavaderos (anti-socavación)
- Rehabilitación de obra hidráulica
- Reposición de piso de arroyo
- Protección contra inundaciones
- Otro (especificar)

**Sección 4: Notas Importantes**
- Notas generales del proyecto
- Notas específicas de la categoría
- Observaciones adicionales

**Características técnicas del PDF PP**:
- **Folio único**: DOP-CPP-{id:05d}-{uuid[:4]}/{año}
  - Ejemplo: DOP-CPP-00001-a3f7/25
- **Almacenamiento**: Modelo `PpFiles` (no `Files`)
- **Relación**: FK a `PpGeneral` y al modelo específico de categoría
- **Layout**: Similar a documento general pero con secciones expandidas
- **Checkboxes**: Representados visualmente en el PDF
- **Tablas dinámicas**: Se generan según campos seleccionados

**Proceso de generación por categoría**:
```python
# 1. Obtener categoría de sesión
cat = request.session.get('categoria', 'sin categoria')

# 2. Obtener datos generales
gen_data = get_object_or_404(PpGeneral, fuuid__uuid=uuid)

# 3. Obtener propuesta específica según categoría
match cat:
    case "parque":
        propuesta = PpParque.objects.filter(fk_pp=gen_data).last()
    case "escuela":
        propuesta = PpEscuela.objects.filter(fk_pp=gen_data).last()
    # ... etc

# 4. Generar folio específico PP
num_folio = gen_pp_folio(gen_data.fuuid)

# 5. Preparar contexto con datos específicos
context = {
    "cat": nombre_categoria,
    "datos": {...},
    "propuesta": {...},  # Campos específicos de la categoría
    "notas_{categoria}": propuesta.notas,
    "folio": num_folio,
    "instalaciones_dict": dict(PpGeneral.INSTALATION_CHOICES),
    "estados_dict": dict(PpGeneral.CHOICES_STATE)
}

# 6. Renderizar y generar PDF
html = render_to_string("documet/pp_document.html", context)
# ... generar PDF
```

### Formatos de Folio

**Trámites de Obra Pública**:
```
DOP-{PUO}-{consecutivo:05d}-{uuid[:4]}/{año:02d}
```
Ejemplos:
- `DOP-OFI-00001-a3f7/25` (Oficio)
- `DOP-CRC-00023-b8e2/25` (CRC)
- `DOP-MEC-00456-c1d9/25` (Marca el Cambio)

**Presupuesto Participativo**:
```
DOP-CPP-{consecutivo:05d}-{uuid[:4]}/{año:02d}
```
Ejemplo:
- `DOP-CPP-00001-a3f7/25`

**Componentes del folio**:
- **DOP**: Gestión de Obra Pública (prefijo fijo)
- **PUO**: Tipo de proceso (OFI, CRC, MEC, DLO, DFE, REG, DEA, EVA, PED, VIN, PPA, CPC)
- **Consecutivo**: Número autoincremental de 5 dígitos
- **UUID**: Primeros 4 caracteres del UUID de sesión
- **Año**: Últimos 2 dígitos del año actual

### Modos de Entrega de PDFs

**1. Descarga Inline (visualización en navegador)**
```python
response["Content-Disposition"] = "inline; filename=documento.pdf"
```
- El PDF se abre directamente en el navegador
- El usuario puede descargar si lo desea
- Rutas: `/ageo/nada/`, `/ageo/document2/`

**2. Guardado en Base de Datos**
```python
# Guardar archivo físico
pdf_file = ContentFile(final_pdf)
file_obj = Files.objects.create(
    nomDoc=nombre_documento,
    fuuid=uuid_obj,
    soli_FK=solicitud,
    finalDoc=pdf_file
)
```
- El PDF se guarda en `media/documents/`
- Se crea registro en tabla `Files`
- Ruta: `/ageo/save/`

**3. Guardado PP en Base de Datos**
```python
# Específico para Presupuesto Participativo
pp_file = PpFiles.objects.create(
    nomDoc=f"PP_{categoria}_{nombre}",
    fuuid=uuid_obj,
    pp_FK=gen_data,
    finalDoc=pdf_file
)
```
- Se guarda en tabla separada `PpFiles`
- Ruta: `/ageo/pp/document`

### Tecnologías y Librerías

**WeasyPrint 66.0**:
- Conversión HTML → PDF
- Soporte completo de CSS3
- Renderizado de imágenes (JPEG, PNG)
- Fuentes personalizadas
- Paginación automática
- Headers y footers

**Bootstrap 5.3.6**:
- Tablas responsivas con clase `table-striped`
- Grid system para layout
- Utilidades de spacing y tipografía

**Django Template Engine**:
- `render_to_string()` para generar HTML
- Context processor para datos dinámicos
- Template tags personalizados

**Static Files**:
- Logo municipal: `static/images/iconChi.png`
- CSS inline en templates para portabilidad del PDF

### Limitaciones y Consideraciones

**Tamaño de archivo**:
- PDFs típicos: 50-500 KB (sin fotos)
- Con fotografías: 500 KB - 5 MB
- Límite configurado en settings: 50 MB por upload

**Rendimiento**:
- Generación de PDF: 1-3 segundos por documento
- Con fotos de alta resolución: hasta 5 segundos
- WeasyPrint es CPU-intensive

**Compatibilidad**:
- PDFs generados compatibles con PDF 1.4+
- Visualización correcta en todos los navegadores modernos
- Impresión optimizada para tamaño carta

**Seguridad**:
- PDFs no están encriptados
- Acceso controlado por autenticación Django
- Archivos servidos por Nginx en producción con headers de seguridad

### Notas de Rendimiento

- Los reportes grandes (>10,000 registros) pueden tardar varios segundos
- Se recomienda usar filtros para limitar el conjunto de datos
- Los archivos Excel generados tienen un límite práctico de ~1 millón de filas
- Las estadísticas se calculan con queries optimizadas (select_related, prefetch_related)
- Cache de 30 días para archivos estáticos de reportes

---

## Flujos de Trabajo

### Flujo 1: Captura de Trámite (AGEO)

```
1. Empleado inicia sesión → /auth/login/
2. Selecciona "Nuevo Trámite" → /ageo/home/
3. Captura datos del ciudadano → /ageo/intData/
4. Captura solicitud → /ageo/soliData/
5. Sube documentos → /ageo/docs/
6. Genera documento final → /ageo/doc/
7. Finaliza trámite → /ageo/clear/
```

### Flujo 2: Presupuesto Participativo

```
1. Datos generales → /ageo/pp/general
2. Selecciona categoría
3. Formulario específico → /ageo/pp/{categoria}
4. Genera PDF → /ageo/pp/document
```

---

## Variables de Entorno

### Variables Requeridas

```env
# Django Core
SECRET_KEY=          # Clave secreta Django (cambiar en producción)
DEBUG=               # False en producción, True en desarrollo
ENVIRONMENT=         # production, development, staging
ALLOWED_HOSTS=       # Dominios permitidos separados por coma

# Base de Datos
DB_ENGINE=           # django.db.backends.mysql
DB_NAME=             # Nombre de la base de datos
DB_USER=             # Usuario de MySQL
DB_PASSWORD=         # Contraseña de MySQL
DB_HOST=             # localhost o IP del servidor
DB_PORT=             # 3306 (default MySQL)

# Redis y Cache
REDIS_URL=           # redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=   # redis://localhost:6379/0
CELERY_RESULT_BACKEND= # redis://localhost:6379/0

# Email
email=               # Email del sistema
contra=              # Contraseña de aplicación
DEFAULT_FROM_EMAIL=  # Email remitente por defecto

# CORS (para APIs)
CORS_ALLOWED_ORIGINS= # Orígenes permitidos separados por coma

# Sentry (Opcional)
SENTRY_DSN=          # DSN de Sentry para monitoreo de errores
SENTRY_TRACES_SAMPLE_RATE= # 0.1 (10% de transacciones)

# HTTPS (Producción)
USE_HTTPS=           # false en desarrollo, true en producción
```

### Variables Opcionales

```env
# Logging
DJANGO_LOG_LEVEL=    # INFO, DEBUG, WARNING, ERROR

# Session
SESSION_COOKIE_AGE=  # 3600 (1 hora)
SESSION_WARNING_TIME= # 300 (5 minutos antes de expirar)
```

---

## Tareas Asíncronas con Celery

### Configuración

El sistema utiliza Celery con Redis como broker para tareas asíncronas y programadas.

```python
# civitas/celery.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### Tareas Implementadas

```python
# portaldu/desUr/tasks.py

@shared_task
def cleanup_old_logs():
    """Limpia logs antiguos (>30 días)"""
    # Ejecuta diariamente vía Celery Beat
    
@shared_task
def send_notification_email(user_email, subject, message, html_message=None):
    """Envía emails de notificación de forma asíncrona"""
    
@shared_task
def process_document_upload(document_id):
    """Procesa documentos subidos (validaciones, OCR, etc.)"""
    
@shared_task
def generate_reports():
    """Genera reportes periódicos del sistema"""
    
@shared_task
def backup_database():
    """Crea respaldos automáticos de la base de datos"""
```

### Ejecución en Desarrollo

```bash
# Terminal 1: Worker
celery -A civitas worker -l info

# Terminal 2: Beat (tareas programadas)
celery -A civitas beat -l info

# Windows (usar scripts incluidos)
start_celery_worker.bat
start_celery_beat.bat
```

### Ejecución en Producción

```bash
# Configurar como servicios systemd
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat
```

---

## Deployment

### Checklist de Producción

**Configuración Django:**
1. `DEBUG = False` en settings.py
2. Configurar `ALLOWED_HOSTS` con dominios específicos
3. Configurar `SECRET_KEY` único y seguro
4. Configurar `ENVIRONMENT = 'production'`

**Base de Datos:**
5. Migrar de SQLite a MySQL 8.0+
6. Ejecutar migraciones: `python manage.py migrate`
7. Recopilar archivos estáticos: `python manage.py collectstatic --noinput`
8. Configurar backups automáticos

**Servidor Web:**
9. Configurar Nginx como proxy inverso
10. Configurar Gunicorn con archivo gunicorn.conf.py
11. Crear servicio systemd para auto-inicio
12. Configurar permisos del socket Unix correctamente

**Seguridad:**
13. Implementar HTTPS con certificados SSL/TLS
14. Configurar headers de seguridad en Nginx:
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
15. Activar `SECURE_SSL_REDIRECT = True`
16. Configurar `SESSION_COOKIE_SECURE = True`
17. Configurar `CSRF_COOKIE_SECURE = True`

**Redis y Celery:**
18. Instalar y configurar Redis
19. Configurar workers de Celery como servicios
20. Configurar Celery Beat para tareas programadas
21. Habilitar django-celery-results para almacenar resultados

**Monitoreo y Logs:**
22. Configurar Sentry para monitoreo de errores
23. Configurar rotación de logs
24. Configurar journald para logs del sistema
25. Implementar health checks

**Optimización:**
26. Configurar workers de Gunicorn según CPU (9 workers recomendados)
27. Habilitar gzip en Nginx
28. Configurar cache de archivos estáticos (30 días)
29. Optimizar queries de base de datos
30. Configurar límites de recursos en systemd

---

## Testing

### Configuración de Tests

El proyecto utiliza pytest y pytest-django para testing:

```bash
# Instalar dependencias de testing
pip install pytest pytest-django factory-boy faker coverage

# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=portaldu --cov-report=html

# Ejecutar tests de un módulo específico
pytest portaldu/cmin/tests/
pytest portaldu/desUr/tests/

# Ver reporte de cobertura
coverage report
coverage html  # Genera reporte HTML en htmlcov/
```

### Estructura de Tests

```
portaldu/
├── cmin/
│   └── tests/
│       ├── test_models.py      # Tests de modelos CMIN
│       ├── test_views.py       # Tests de vistas CMIN
│       ├── test_api.py         # Tests de API REST
│       └── test_forms.py       # Tests de formularios
└── desUr/
    └── tests/
        ├── test_models.py      # Tests de modelos DesUr
        ├── test_views.py       # Tests de vistas DesUr
        ├── test_api.py         # Tests de API REST
        ├── test_serializers.py # Tests de serializers
        └── test_services.py    # Tests de servicios
```

### Factories para Testing

El proyecto usa Factory Boy para generar datos de prueba:

```python
# Ejemplo de uso
from portaldu.cmin.tests.factories import UserFactory

# Crear usuario de prueba
user = UserFactory(rol='administrador')

# Crear múltiples usuarios
users = UserFactory.create_batch(10)
```

---

## Documentación de Código

### Estado de Documentación

| Módulo | Archivo | Líneas | Estado |
|--------|---------|--------|--------|
| **CMIN** | `models.py` | 904 | 100% |
| **CMIN** | `views.py` | 1469 | 100% |
| **CMIN** | `api_views.py` | 567 | 100% |
| **CMIN** | `serializers.py` | 138 | 100% |
| **CMIN** | `forms.py` | 538 | 100% |
| **CMIN** | `urls.py` | 122 | 100% |
| **CMIN** | `api_urls.py` | 46 | 100% |
| **AGEO** | `models.py` | 558 | 100% |
| **AGEO** | `views.py` | ~2000 | 100% |
| **AGEO** | `api_views.py` | 556 | 100% |
| **AGEO** | `serializers.py` | 438 | 100% |
| **AGEO** | `forms.py` | 817 | 100% |
| **AGEO** | `urls.py` | 300 | 100% |
| **AGEO** | `api_urls.py` | 198 | 100% |
| **AGEO** | `auth.py` | 147 | 100% |
| **AGEO** | `services.py` | 1014 | 100% |
| **AGEO** | `WSDService.py` | 417 | 100% |
| **AGEO** | `tasks.py` | 145 | 100% |
| **AGEO** | `middleware.py` | 50 | 100% |
| **Principal** | `urls.py` | 336 | 100% |
| **Principal** | `settings.py` | 436 | 100% |
| **Principal** | `celery.py` | 35 | 100% |

**Total**: ~11,000+ líneas de documentación en 22 archivos principales

### Características de la Documentación

- Docstrings detallados en español para todas las clases y funciones
- Documentación de parámetros y valores de retorno
- Ejemplos de uso en código
- Comentarios inline explicativos
- Documentación de formato de folios
- Diagramas de flujo en código
- Notas de seguridad y producción

---

## Licencia

Este proyecto está bajo la licencia **BSD License**.

---

## Equipo de Desarrollo

- **Desarrollador Principal**: Arturo
- **Organización**: Dirección de Obras Públicas Municipales
- **Municipio**: Chihuahua, Chihuahua

---

## Soporte y Recursos

- **Documentación API**: `/swagger/` y `/redoc/`
- **Panel de Administración**: `/admin/`
- **Repositorio**: GitHub (privado)
- **Documentación Técnica**:
  - `INTEGRACIONES_IMPLEMENTADAS.md` - Detalle de integraciones
  - `EVALUACION_FINAL_DESPLIEGUE.md` - Checklist de deployment
  - `Manual_Usuario_CMIN.md` - Manual de usuario CMIN
  - `Manual_Usuario_DesUr.md` - Manual de usuario AGEO

---

**Última actualización**: Diciembre 2025  
**Estado del Proyecto**: Producción  
**Cobertura de Documentación**: 100% archivos críticos  
**Versión Django**: 5.0  
**Versión Python**: 3.11+

---

## Glosario de Términos

**CIVITAS**: Nombre del proyecto
**CMIN**: Módulo de administradores
**AGEO**: Sistema de gestión de obra pública (anteriormente DesUr)  
**DesUr**: (nombre legacy del módulo AGEO)
**DOP**: Dirección de Obras Públicas (prefijo de folios)
**PUO**: Proceso Unidad Operativa (tipo de proceso administrativo)  
**PP**: Presupuesto Participativo  
**CURP**: Clave Única de Registro de Población

---

<div align="center">
  <strong> AGEO - Atención, gestión inteligente</strong><br>
</div>

