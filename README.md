# 🏛️ AGEO - Sistema Integrado de Gestión de Trámites Ciudadanos

**Versión**: 1.0.0  
**Proyecto**: AGEO 2025  
**Framework**: Django 4.2+ | Python 3.10+  
**Estado**: Producción

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
**Gestión de licitaciones** de obra pública <!--✅ **Geolocalización** de proyectos y problemas reportados-->  
**APIs REST** para integración con aplicaciones externas  
**Documentación automática** de APIs con Swagger/ReDoc  
**Sistema de autenticación unificado** con roles y permisos  
**Reportes y estadísticas** en tiempo real  

### Tecnologías Utilizadas

| Categoría           | Tecnología                                          |
|---------------------|-----------------------------------------------------|
| **Backend**         | Django 4.2+, Django REST Framework                  |
| **Base de Datos**   | MySQL (desarrollo), MySQL (producción)              |
| **Frontend**        | HTML5, CSS3, JavaScript, Bootstrap 5                |
| **PDF Generation**  | WeasyPrint                                          |
| **APIs**            | DRF, drf-yasg (Swagger)                             |
| **Geolocalización** | OpenStreetMap, Leaflet.js, WSDomicilios Municipales |
| **Autenticación**   | Django Auth, Session-based                          |
| **Async Tasks**     | Celery (opcional)                                   |
| **Servidor**        | Nginx, Ubuntu server 22                             |

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

## 🔧 Módulos del Sistema

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

| Código | Descripción                          | Formato Folio |
|--------|--------------------------------------|---------------|
| `OFI` | Oficio                               | GOP-OFI-#####-XXXX/YY |
| `CRC` | CRC                                  | GOP-CRC-#####-XXXX/YY |
| `MEC` | Marca el cambio                      | GOP-MEC-#####-XXXX/YY |
| `DLO` | Diputado Local                       | GOP-DLO-#####-XXXX/YY |
| `DFE` | Diputado Federal                     | GOP-DFE-#####-XXXX/YY |
| `REG` | Regidores                            | GOP-REG-#####-XXXX/YY |
| `DEA` | Despacho del Alcalde                 | GOP-DEA-#####-XXXX/YY |
| `EVA` | Evento con el Alcalde                | GOP-EVA-#####-XXXX/YY |
| `PED` | Presencial en Dirección              | GOP-PED-#####-XXXX/YY |
| `VIN` | Vinculación                          | GOP-VIN-#####-XXXX/YY |
| `PPA` | Presupuesto Participativo            | GOP-PPA-#####-XXXX/YY |
| `CPC` | Coordinación Participación Ciudadana | GOP-CPC-#####-XXXX/YY |

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

Configuración dentro de un servidor Linux (ubunut) por medio de en
un archivo de configuración en la carpeta de nginx y otro en la carpeta
system

```bash
/etc/nginx/sites-available/civitas
/etc/systemd/system/civitas.conf
```

---

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
SECRET_KEY=          # Clave secreta Django
DEBUG=               # True/False
ALLOWED_HOSTS=       # Dominios permitidos
DB_ENGINE=           # Motor de base de datos
DB_NAME=             # Nombre de BD
EMAIL_BACKEND=       # Backend de email
```

---

## Deployment

### Checklist de Producción

1. `DEBUG = False`
2. Configurar `ALLOWED_HOSTS`
3. Base de datos MySQL
4. Configurar Nginx
5. Configurar Gunicorn
6. HTTPS con certificados SSL (ver con área de sistemas)
7. Collectstatic
8. Migraciones actualizadas
9. Backups automáticos
10. Monitoring y logs

---

## Documentación de Código

### Estado de Documentación

| Módulo | Archivo | Estado |
|--------|---------|--------|
| **AGEO** | `views.py` | 100% |
| **AGEO** | `api_views.py` | 100% |
| **AGEO** | `serializers.py` | 100% |
| **AGEO** | `forms.py` | 100% |
| **AGEO** | `urls.py` | 100% |
| **AGEO** | `api_urls.py` | 100% |
| **AGEO** | `auth.py` | 100% |
| **Principal** | `urls.py` | 100% |

**Total**: ~6,000 líneas de documentación en 8 archivos principales

---

## Licencia

Este proyecto está bajo la licencia **BSD License**.

---

## Equipo de Desarrollo

- **Desarrollado por**: Arturo
- **Organización**: Dirección de Obras Públicas Municipales

---

## Soporte

- **Documentación**: `/swagger/` y `/redoc/`

---

**Última actualización**: Diciembre 2025  
**Estado del Proyecto**: Producción  
**Cobertura de Documentación**: 100% archivos críticos

---

---
## Glosario

**WIP**: Work In Progress
**WIP?**: Work In Progress (Consultar)
---

<div align="center">
  <strong> AGEO - Atención, gestión inteligente</strong><br>
</div>

