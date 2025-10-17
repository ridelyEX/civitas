"""
URLs principales del proyecto CIVITAS
Sistema de enrutamiento central que coordina todos los módulos del sistema

Este archivo configura el enrutamiento principal del proyecto Civitas,
que es un sistema integrado de gestión de trámites ciudadanos compuesto por dos módulos:

MÓDULOS DEL SISTEMA:
==================

1. CMIN (Centro Municipal de Información)
   - Ruta base: /cmin/
   - API: /api/cmin/
   - Funcionalidades:
     * Atención ciudadana presencial
     * Gestión de licitaciones de obra pública
     * Reportes y estadísticas
     * Sistema de usuarios unificado
     * Validación de documentos

2. AGEO (Anteriormente DesUr)
   - Ruta base: /ageo/
   - API: /api/ageo/
   - Funcionalidades:
     * Captura de trámites en campo
     * Presupuesto participativo
     * Gestión de solicitudes ciudadanas
     * Generación de documentos PDF
     * Geolocalización de proyectos

AUTENTICACIÓN:
==============
El sistema usa autenticación unificada compartida entre ambos módulos.
Los usuarios tienen roles que determinan a qué módulos pueden acceder:
- Empleados CMIN: Solo acceso a CMIN
- Empleados DesUr/AGEO: Solo acceso a AGEO
- Administradores: Acceso a ambos módulos
- Superusuarios: Acceso total incluyendo panel de administración

APIS REST:
==========
Ambos módulos exponen APIs REST para integración con aplicaciones externas:
- /api/ageo/ - API de trámites de campo (DesUr)
- /api/cmin/ - API de atención ciudadana (CMIN)

DOCUMENTACIÓN AUTOMÁTICA:
=========================
El sistema usa drf-yasg (Yet Another Swagger Generator) para generar
documentación interactiva de las APIs automáticamente.

Endpoints de documentación disponibles:
- /swagger/ - Interfaz Swagger UI (interactiva, permite probar endpoints)
- /redoc/ - Interfaz ReDoc (documentación estática, mejor para lectura)
- /api/docs/ - Alias de Swagger (mismo que /swagger/)
- /swagger.json - Esquema OpenAPI en formato JSON

RUTAS PRINCIPALES:
==================
/admin/          - Panel de administración de Django
/cmin/           - Módulo de Centro Municipal de Información
/ageo/           - Módulo de Gestión de Obra Pública (DesUr)
/api/cmin/       - API REST de CMIN
/api/ageo/       - API REST de AGEO
/swagger/        - Documentación interactiva de APIs
/redoc/          - Documentación ReDoc de APIs

ARCHIVOS ESTÁTICOS Y MEDIA:
===========================
En desarrollo (DEBUG=True):
- /media/ - Archivos subidos por usuarios (fotos, documentos, PDFs)
- /static/ - Archivos estáticos (CSS, JS, imágenes del sistema)

En producción (DEBUG=False):
- Estos archivos deben ser servidos por nginx u otro servidor web
- Django no sirve archivos estáticos en producción por rendimiento

SEGURIDAD:
==========
- CSRF protection habilitado en todas las vistas que no sean API
- APIs REST sin autenticación (TODO: implementar en producción)
- Panel de administración requiere superusuario
- Acceso a módulos controlado por decoradores @login_required

NOTAS DE DESARROLLO:
====================
- El nombre 'ageo' es un alias de 'desUr' (Desarrollo Urbano)
- Ambos módulos comparten el modelo Users de CMIN
- Las URLs están organizadas jerárquicamente por módulo
- Swagger está configurado con AllowAny para facilitar desarrollo
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ============================================================================
# CONFIGURACIÓN DE SWAGGER - Documentación automática de APIs
# ============================================================================

# Configurar el generador de esquemas de Swagger/OpenAPI
# Esto crea la documentación interactiva que se puede ver en /swagger/ y /redoc/
schema_view = get_schema_view(
   openapi.Info(
      # Información general de la API mostrada en la documentación
      title="Civitas API",                                    # Título principal
      default_version='v1',                                   # Versión de la API
      description="API para el sistema de trámites Civitas", # Descripción breve
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contacto@civitas.gov.mx"),  # Contacto de soporte
      license=openapi.License(name="BSD License"),            # Licencia del proyecto
   ),
   public=True,                                               # API pública (visible sin autenticación)
   permission_classes=(permissions.AllowAny,),                # ⚠️ TODO: Cambiar en producción a IsAuthenticated
)

# ============================================================================
# RUTAS PRINCIPALES DEL PROYECTO
# ============================================================================

urlpatterns = [
    # ========================================================================
    # PANEL DE ADMINISTRACIÓN DE DJANGO
    # ========================================================================

    # Panel de administración para superusuarios
    # Permite gestión completa de:
    # - Usuarios y permisos
    # - Modelos de datos (ciudadanos, solicitudes, licitaciones, etc.)
    # - Logs del sistema
    # - Configuraciones generales
    # Acceso: Solo superusuarios (is_superuser=True)
    # URL: /admin/
    path('admin/', admin.site.urls),

    # ========================================================================
    # APIs REST - Endpoints para integración con aplicaciones externas
    # ========================================================================

    # API del módulo AGEO (DesUr - Desarrollo Urbano)
    # Endpoints disponibles:
    #   - POST /api/ageo/uuid/        - Crear sesión UUID
    #   - POST /api/ageo/data/        - Enviar datos de ciudadano
    #   - POST /api/ageo/soli/        - Crear solicitud de trámite
    #   - POST /api/ageo/files/       - Subir documentos
    #   - GET  /api/ageo/ciudadanos/  - Listar ciudadanos (paginado)
    #   - + CRUD completo de ciudadanos
    # Permisos: AllowAny (⚠️ cambiar en producción)
    # Documentación detallada: Ver portaldu/desUr/api_urls.py
    path('api/ageo/', include('portaldu.desUr.api_urls')),

    # API del módulo CMIN (Centro Municipal de Información)
    # Endpoints disponibles:
    #   - Gestión de usuarios y autenticación
    #   - Consulta de licitaciones
    #   - Reportes y estadísticas
    #   - Validación de documentos
    # Permisos: Varía según endpoint
    # Documentación detallada: Ver portaldu/cmin/api_urls.py
    path('api/cmin/', include('portaldu.cmin.api_urls')),

    # ========================================================================
    # APLICACIONES PRINCIPALES - Módulos del sistema
    # ========================================================================

    # Módulo AGEO (Desarrollo Urbano - DesUr)
    # Sistema de captura de trámites en campo y presupuesto participativo
    #
    # Rutas principales incluidas:
    #   /ageo/                    - Menú principal (dashboard)
    #   /ageo/auth/*              - Autenticación y configuración de usuario
    #   /ageo/home/               - Inicio de nuevo trámite
    #   /ageo/intData/            - Captura de datos del ciudadano
    #   /ageo/soliData/           - Captura de solicitud
    #   /ageo/pp/*                - Presupuesto participativo (6 rutas)
    #   /ageo/docs/               - Gestión de documentos adjuntos
    #   /ageo/pago/               - Pagos de licitaciones
    #   /ageo/geocode/            - Servicios de geolocalización
    #
    # Permisos: Requiere @login_required y @desur_access_required
    # Ver documentación completa: portaldu/desUr/urls.py
    path('ageo/', include('portaldu.desUr.urls')),

    # Módulo CMIN (Centro Municipal de Información)
    # Sistema de atención ciudadana presencial y gestión de licitaciones
    #
    # Rutas principales incluidas:
    #   /cmin/                    - Dashboard principal
    #   /cmin/auth/*              - Sistema de autenticación unificado
    #   /cmin/licitaciones/*      - Gestión de licitaciones (CRUD completo)
    #   /cmin/reportes/           - Generación de reportes
    #   /cmin/validacion/         - Validación de documentos
    #   /cmin/estadisticas/       - Dashboard de estadísticas
    #
    # Permisos: Requiere @login_required y @cmin_access_required
    # Sistema de autenticación: Centralizado en este módulo
    # Ver documentación completa: portaldu/cmin/urls.py
    path('cmin/', include('portaldu.cmin.urls')),

    # ========================================================================
    # DOCUMENTACIÓN AUTOMÁTICA DE APIs - Swagger/ReDoc
    # ========================================================================

    # Esquema JSON de la API en formato OpenAPI 2.0/3.0
    # Útil para:
    # - Importar en Postman o Insomnia
    # - Generar clientes automáticamente
    # - Integración con herramientas de testing
    # URL: /swagger.json o /swagger.yaml
    # Formato: Se define con <format> (.json o .yaml)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Interfaz Swagger UI - Documentación interactiva
    # Características:
    # - Exploración interactiva de endpoints
    # - Prueba de endpoints directamente desde el navegador
    # - Visualización de modelos de datos
    # - Ejemplos de request/response
    # - Descarga de esquemas
    # URL: /swagger/
    # Ideal para: Desarrollo y testing de APIs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Interfaz ReDoc - Documentación estática elegante
    # Características:
    # - Presentación limpia y profesional
    # - Mejor para lectura y referencia
    # - Navegación por menú lateral
    # - Búsqueda de endpoints
    # - Exportación a PDF
    # URL: /redoc/
    # Ideal para: Documentación para usuarios finales de la API
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Alias de Swagger UI en ruta /api/docs/
    # Proporciona acceso a la documentación en una URL más semántica
    # URL: /api/docs/
    # Funcionalidad: Idéntica a /swagger/
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS Y MEDIA (Solo en desarrollo)
# ============================================================================

# Servir archivos MEDIA y STATIC solo en modo DEBUG (desarrollo)
# En producción (DEBUG=False), nginx u otro servidor web debe manejar estos archivos
if settings.DEBUG:
    # Servir archivos MEDIA (subidos por usuarios)
    # Incluye:
    # - Fotos de ciudadanos
    # - Documentos adjuntos (PDFs, imágenes)
    # - Documentos generados (trámites, comprobantes)
    # - Fotos de problemas reportados
    # Ubicación física: /media/ (definido en settings.MEDIA_ROOT)
    # URL: /media/{ruta_archivo}
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Servir archivos STATIC (recursos del sistema)
    # Incluye:
    # - CSS y JavaScript
    # - Imágenes del sistema (logos, iconos)
    # - Archivos de bibliotecas (Bootstrap, jQuery, etc.)
    # - Archivos de administración de Django
    # Ubicación física: /staticfiles/ (definido en settings.STATIC_ROOT)
    # URL: /static/{ruta_archivo}
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# NOTAS PARA PRODUCCIÓN
# ============================================================================
#
# Al desplegar a producción, asegurarse de:
#
# 1. DEBUG = False en settings.py
#    - Esto desactiva el servidor de archivos estáticos de Django
#    - Oculta información sensible en errores
#    - Mejora significativamente el rendimiento
#
# 2. Configurar nginx para servir archivos estáticos:
#    location /media/ {
#        alias /ruta/al/proyecto/media/;
#    }
#    location /static/ {
#        alias /ruta/al/proyecto/staticfiles/;
#    }
#
# 3. Ejecutar collectstatic antes de desplegar:
#    python manage.py collectstatic --noinput
#    - Esto recopila todos los archivos estáticos en STATIC_ROOT
#
# 4. Configurar ALLOWED_HOSTS en settings.py:
#    ALLOWED_HOSTS = ['civitas.gov.mx', 'www.civitas.gov.mx']
#
# 5. Implementar HTTPS:
#    - Configurar certificados SSL en nginx
#    - Activar SECURE_SSL_REDIRECT = True
#    - Configurar SECURE_PROXY_SSL_HEADER
#
# 6. Cambiar permisos de Swagger:
#    permission_classes=(permissions.IsAuthenticated,)
#    - Proteger documentación de API en producción
#
# 7. Configurar base de datos de producción:
#    - PostgreSQL recomendado sobre SQLite
#    - Configurar backups automáticos
#    - Optimizar índices
#
# 8. Configurar logging:
#    - Logs de errores a archivo
#    - Logs de acceso separados
#    - Rotación de logs
#
# 9. Implementar rate limiting en APIs:
#    - Prevenir abuso de endpoints
#    - Proteger contra ataques DDoS
#
# 10. Revisar configuración de CORS si aplica:
#     - Configurar dominios permitidos
#     - Restringir métodos y headers
#
# ============================================================================

