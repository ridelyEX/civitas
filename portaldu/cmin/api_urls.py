"""
URLs de la API REST del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema de rutas para endpoints de aplicaciones móviles

Este módulo define todas las rutas de la API REST del sistema CIVITAS - CMIN,
especializadas en la comunicación con aplicaciones móviles de encuestas
y servicios de sincronización de datos offline.

Funcionalidades principales:
- Endpoints para aplicaciones móviles AGEO
- Rutas de sincronización de encuestas offline
- APIs de gestión de encuestas online
- Servicios de estadísticas y monitoreo
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AgeoMobileViewSet

# === CONFIGURACIÓN DEL ROUTER DE DRF ===

# Router principal para endpoints automáticos de Django REST Framework
# Genera automáticamente rutas estándar (GET, POST, PUT, DELETE) para ViewSets
router = DefaultRouter()

# Registrar ViewSet de aplicaciones móviles AGEO
# Basename: 'ageo_mobile' - Identificador único para el conjunto de rutas
# Genera rutas automáticas para:
# - GET /ageo_mobile/ - Listar encuestas
# - POST /ageo_mobile/ - Crear encuesta
# - GET /ageo_mobile/{id}/ - Detalle de encuesta
# - PUT /ageo_mobile/{id}/ - Actualizar encuesta
# - DELETE /ageo_mobile/{id}/ - Eliminar encuesta
router.register(r'ageo_mobile', AgeoMobileViewSet, basename='ageo_mobile')

# === PATRONES DE URLs DE LA API ===

urlpatterns = [
    # Incluir todas las rutas del router bajo el prefijo 'encuestas/'
    # Rutas resultantes:
    # - /api/encuestas/ageo_mobile/ - Endpoints principales
    # - /api/encuestas/ageo_mobile/recibir_encuesta_offline/ - Sincronización offline
    # - /api/encuestas/ageo_mobile/recibir_encuesta_online/ - Encuestas online
    # - /api/encuestas/ageo_mobile/status_sincronizacion/ - Estado del servicio
    path('encuestas/', include(router.urls))
]