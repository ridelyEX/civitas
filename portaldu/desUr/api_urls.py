"""
API URLs del módulo DesUr (Desarrollo Urbano)
Sistema de enrutamiento para APIs REST de integración externa

Este módulo define las rutas de la API REST para el sistema DesUr,
permitiendo la integración con aplicaciones móviles y servicios externos.

Endpoints Principales:
- /api_sol/ciudadanos/ - CRUD completo de ciudadanos
- /api_sol/uuid/ - Creación de UUIDs de sesión
- /api_sol/data/ - Envío de datos de ciudadanos
- /api_sol/soli/ - Creación de solicitudes de trámites
- /api_sol/files/ - Subida de archivos/documentos

Autenticación:
- Actualmente usa AllowAny (sin autenticación)
- TODO: Implementar autenticación por token para producción
- Considerar JWT o Token Authentication de DRF

Uso Típico:
1. POST /api_sol/uuid/ - Obtener UUID de sesión
2. POST /api_sol/data/ - Enviar datos del ciudadano
3. POST /api_sol/soli/ - Crear solicitud de trámite
4. POST /api_sol/files/ - Subir documentos adjuntos

Formato de Respuestas:
Todas las respuestas siguen el formato:
{
    'status': 'success' | 'error',
    'message': str,
    'data': dict (opcional),
    'errors': dict (opcional en caso de error)
}
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from .api_views import get_token

# Router para ViewSets - Proporciona CRUD completo automático
# Registra CiudadanosViewSet para operaciones estándar de REST
router = DefaultRouter()

# Registro del ViewSet de ciudadanos
# Genera automáticamente las siguientes rutas:
#   - GET    /ciudadanos/          - Listar ciudadanos (con paginación y búsqueda)
#   - POST   /ciudadanos/          - Crear nuevo ciudadano
#   - GET    /ciudadanos/{id}/     - Obtener detalle de ciudadano específico
#   - PUT    /ciudadanos/{id}/     - Actualizar ciudadano completo
#   - PATCH  /ciudadanos/{id}/     - Actualizar ciudadano parcial
#   - DELETE /ciudadanos/{id}/     - Eliminar ciudadano
router.register(r'ciudadanos', api_views.CiudadanosViewSet, basename='ciudadano')

urlpatterns = [
    # ============================================================================
    # CRUD AUTOMÁTICO - Rutas generadas por el router
    # ============================================================================

    # Incluir todas las URLs del router (CRUD completo de ciudadanos)
    # Ver arriba para lista completa de endpoints generados
    path('', include(router.urls)),

    # ============================================================================
    # ENDPOINTS PERSONALIZADOS - Multipropósito para aplicaciones externas
    # ============================================================================

    # Crear UUID de sesión
    # POST /api_sol/uuid/
    # Request body: {} (vacío, se genera automáticamente)
    # Response: {'status': 'success', 'data': {'prime': int, 'uuid': str}}
    # Uso: Iniciar una nueva sesión de captura de trámite
    path('uuid/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-uuid'),

    # Enviar datos de ciudadano
    # POST /api_sol/data/
    # Request body: {
    #     'fuuid': str|int,           # UUID de sesión obtenido en paso anterior
    #     'nombre': str,              # Nombre del ciudadano
    #     'pApe': str,                # Apellido paterno
    #     'mApe': str,                # Apellido materno
    #     'bDay': str,                # Fecha nacimiento (YYYY-MM-DD o DD/MM/YYYY)
    #     'tel': str,                 # Teléfono (10-15 dígitos)
    #     'curp': str,                # CURP (18 caracteres)
    #     'sexo': str,                # Género (H/M o hombre/mujer)
    #     'dirr': str,                # Dirección completa
    #     'asunto': str,              # Código del trámite (DOP00001-DOP00013)
    #     'etnia': str (opcional),    # Grupo étnico
    #     'disc': str (opcional),     # Discapacidad
    #     'vul': str (opcional)       # Grupo vulnerable
    # }
    # Response: {'status': 'success', 'data': {'data_ID': int}}
    # Validaciones: CURP único, formato de fecha, teléfono válido
    path('data/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-data'),

    # Crear solicitud de trámite
    # POST /api_sol/soli/
    # Request body: {
    #     'data_ID': int,             # ID del ciudadano (obtenido en paso anterior)
    #     'dirr': str,                # Dirección específica del problema
    #     'info': str,                # Información adicional
    #     'descc': str,               # Descripción detallada del problema
    #     'foto': file (opcional),    # Imagen del problema
    #     'puo': str,                 # Tipo de proceso (OFI, CRC, MEC, etc.)
    #     'folio': str (opcional)     # Se genera automáticamente si no se provee
    # }
    # Response: {'status': 'success', 'data': {'soli_ID': int}}
    # Validaciones: data_ID debe existir, PUO debe ser válido
    # PUOs válidos: OFI, CRC, MEC, DLO, DFE, REG, DEA, EVA, PED, VIN, PPA, CPC
    path('soli/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-soli'),

    # Subir archivo/documento final
    # POST /api_sol/files/
    # Content-Type: multipart/form-data
    # Request body: {
    #     'fuuid': str,               # UUID de sesión
    #     'soli_FK': int (opcional),  # ID de solicitud asociada
    #     'nomDoc': str,              # Nombre del documento
    #     'finalDoc': file            # Archivo PDF del documento final
    # }
    # Response: {'status': 'success', 'data': {'fDoc_ID': int}}
    # Validaciones: UUID debe existir, archivo debe ser válido
    # Límite de tamaño: 5 MB por archivo
    path('files/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-files'),

    # ============================================================================
    # ENDPOINTS FUTUROS - Actualmente comentados
    # ============================================================================

    # Subida de PDF de solicitud (por implementar)
    # TODO: Implementar endpoint específico para PDFs de solicitudes
    # path('solicitudes/upload-pdf/', api_views.upload_pdf_view, name='api-upload-pdf'),

    # ============================================================================
    # AUTENTICACIÓN - Sistema en desarrollo
    # ============================================================================

    # Endpoints de autenticación (comentados hasta implementar)
    path('auth/token/', get_token, name='api-token'),
    # TODO: Considerar usar JWT para mayor seguridad

    # Login via API
    # POST /api_sol/login/
    # Request: {'username': str, 'password': str}
    # Response: {'token': str, 'user': {...}}
    # path('login/', api_views.api_login, name='api-login'),

    # Logout via API
    # POST /api_sol/logout/
    # Headers: Authorization: Token {token}
    # Response: {'status': 'success'}
    # path('logout/', api_views.api_logout, name='api-logout'),

    # Perfil de usuario autenticado
    # GET /api_sol/profile/
    # Headers: Authorization: Token {token}
    # Response: {'user': {...}}
    # path('profile/', api_views.api_profile, name='api-profile'),

]

# ============================================================================
# NOTAS DE SEGURIDAD PARA PRODUCCIÓN
# ============================================================================
#
# IMPORTANTE: Antes de desplegar a producción, implementar:
#
# 1. Autenticación por Token:
#    - Instalar: pip install djangorestframework-simplejwt
#    - Configurar JWT en settings.py
#    - Requerir autenticación en todos los endpoints
#
# 2. Throttling (límite de peticiones):
#    REST_FRAMEWORK = {
#        'DEFAULT_THROTTLE_CLASSES': [
#            'rest_framework.throttling.AnonRateThrottle',
#            'rest_framework.throttling.UserRateThrottle'
#        ],
#        'DEFAULT_THROTTLE_RATES': {
#            'anon': '100/day',
#            'user': '1000/day'
#        }
#    }
#
# 3. CORS (si se accede desde diferentes dominios):
#    - Instalar: pip install django-cors-headers
#    - Configurar dominios permitidos en settings.py
#
# 4. HTTPS:
#    - Forzar uso de HTTPS en producción
#    - Configurar SECURE_SSL_REDIRECT = True
#
# 5. Validación de origen:
#    - Verificar headers de origen de peticiones
#    - Implementar whitelist de IPs permitidas si es necesario
#
# ============================================================================
