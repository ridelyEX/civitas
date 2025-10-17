"""
URLs del módulo DesUr (Desarrollo Urbano)
Sistema de enrutamiento para trámites de obra pública y desarrollo urbano

Este módulo define todas las rutas URL del sistema DesUr, incluyendo:
- Autenticación y gestión de usuarios
- Captura de datos de ciudadanos y solicitudes
- Presupuesto participativo
- Generación de documentos PDF
- APIs REST para integración externa
- Servicios de geocodificación

Estructura de URLs:
- /ageo/ - Menú principal (requiere autenticación)
- /ageo/auth/* - Rutas de autenticación y configuración de usuario
- /ageo/pp/* - Presupuesto participativo
- /ageo/api_sol/* - API REST para aplicaciones externas
- /ageo/geocode/ - Servicios de geolocalización

Permisos:
- Todas las rutas requieren autenticación y rol con acceso a DesUr
- Las APIs REST usan AllowAny pero deberían revisarse para producción
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para APIs REST (actualmente comentado)
# Descomentar cuando se implemente FilesViewSet para gestión de archivos vía API
# router = DefaultRouter()
# router.register(r'files', views.FilesViewSet, basename='files')

urlpatterns = [
    # ============================================================================
    # API REST - Endpoints para integración con aplicaciones externas
    # ============================================================================

    # Incluir URLs de la API de solicitudes
    # Endpoints disponibles en api_urls.py:
    #   - POST /api_sol/ciudadanos/ - Crear/listar ciudadanos
    #   - POST /api_sol/recibir_datos/ - Endpoint multipropósito
    path('api_sol/', include('portaldu.desUr.api_urls')),

    # ============================================================================
    # AUTENTICACIÓN - Sistema unificado con CMIN
    # ============================================================================

    # Login de DesUr (redirige al sistema unificado)
    # GET - Muestra mensaje y redirige a /auth/login/
    # Mantiene compatibilidad con URLs antiguas
    path('auth/login/', views.desur_login_view, name='desur_login'),

    # Logout de DesUr (redirige al sistema unificado)
    # GET - Cierra sesión y redirige
    # Mantiene compatibilidad con URLs antiguas
    path('auth/logout/', views.desur_logout_view, name='desur_logout'),

    # Configuración de perfil de usuario
    # GET - Muestra formulario de configuración
    # POST - Guarda cambios en perfil (nombre, foto, contraseña, etc.)
    # Requiere: @login_required, @desur_access_required
    path('auth/user_conf/', views.desur_user_conf, name='desur_user_conf'),

    # Menú principal de DesUr (dashboard)
    # GET - Muestra dashboard con opciones de captura de trámites
    # Requiere: @login_required, @desur_access_required
    # Template: main.html
    path('', views.desur_menu, name='desur_menu'),

    # ============================================================================
    # HISTORIAL Y BÚSQUEDA DE TRÁMITES
    # ============================================================================

    # Historial de trámites procesados por el empleado actual
    # GET - Lista paginada de trámites procesados (10 por página)
    # Query params: ?page=N
    # Requiere: @login_required, @desur_access_required
    # Template: auth/desur_historial.html
    path('auth/historial/', views.desur_historial, name='desur_historial'),

    # Búsqueda avanzada de trámites
    # GET - Busca por folio, nombre, CURP, etc.
    # Query params: ?q=término_búsqueda
    # Requiere: @login_required, @desur_access_required
    # Template: auth/desur_buscar.html
    path('auth/buscar/', views.desur_buscar_tramite, name='desur_buscar'),

    # ============================================================================
    # PRESUPUESTO PARTICIPATIVO - Captura de propuestas ciudadanas
    # ============================================================================

    # Formulario de datos generales del proyecto PP
    # GET - Muestra formulario GeneralRender
    # POST - Guarda datos y redirige según categoría seleccionada
    # Categorías: parque, escuela, cs, infraestructura, pluviales
    # Requiere: @login_required, @desur_access_required
    # Template: pp/datos_generales.html
    path('pp/general', views.gen_render, name='general'),

    # Formulario específico para propuestas en ESCUELAS
    # GET - Muestra formulario EscuelaRender
    # POST - Guarda propuesta de escuela y genera documento
    # Campos: rehabilitación, construcción, canchas deportivas
    # Template: pp/escuela.html
    path('pp/escuelas', views.escuela_render, name='escuelas'),

    # Formulario específico para propuestas en PARQUES
    # GET - Muestra formulario ParqueRender
    # POST - Guarda propuesta de parque y genera documento
    # Campos: canchas, alumbrado, juegos, techumbres, equipamiento
    # Template: pp/parque.html
    path('pp/parques', views.parque_render, name='parques'),

    # Formulario para CENTROS COMUNITARIOS y SALONES DE USOS MÚLTIPLES
    # GET - Muestra formulario CsRender
    # POST - Guarda propuesta de centro/salón y genera documento
    # Campos: rehabilitación, construcción de espacios
    # Template: pp/centro_salon.html
    path('pp/centros', views.cs_render, name='centros'),

    # Formulario específico para propuestas de INFRAESTRUCTURA
    # GET - Muestra formulario InfraestructuraRender
    # POST - Guarda propuesta de infraestructura y genera documento
    # Campos: bardas, banquetas, pavimentación, señalamiento
    # Template: pp/infraestructura.html
    path('pp/infraestructura', views.infraestructura_render, name='infraestructura'),

    # Formulario específico para SOLUCIONES PLUVIALES
    # GET - Muestra formulario PluvialRender
    # POST - Guarda propuesta pluvial y genera documento
    # Campos: muros, canalizaciones, puentes, rejillas, obras hidráulicas
    # Template: pp/pluviales.html
    path('pp/pluviales', views.pluvial_render, name='pluviales'),

    # Generación de documento PDF de Presupuesto Participativo
    # GET - Genera PDF según categoría guardada en session
    # Guarda archivo en PpFiles y muestra confirmación
    # Folio format: GOP-CPP-#####-XXXX/YY
    # Template: documet/save.html (confirmación)
    path('pp/document', views.pp_document, name='pp_document'),

    # ============================================================================
    # OBRA PÚBLICA - Flujo principal de captura de trámites
    # ============================================================================

    # Confirmación de guardado de documento
    # GET - Muestra página de confirmación después de guardar
    # Requiere cookie 'uuid' válida
    # Template: documet/save.html
    path('base/', views.base, name='base'),

    # Generación de documento PDF para descarga inmediata
    # GET - Genera PDF del trámite y lo muestra inline en navegador
    # Requiere: cookie 'uuid', datos ciudadano, solicitud completa
    # Content-Type: application/pdf
    # Template renderizado: documet/document.html
    path('nada/', views.document, name="document"),

    # Inicio de nuevo trámite - Selección de tipo
    # GET - Muestra opciones: Obra Pública (op) o Presupuesto Participativo (pp)
    # POST - Crea/valida UUID y redirige según action seleccionado
    # Actions: 'op' -> /intData/, 'pp' -> /pp/general
    # Establece cookie 'uuid' con duración de 1 hora
    # Template: main.html
    path('home/', views.home, name="home"),

    # Captura de datos personales del CIUDADANO
    # GET - Muestra formulario de datos personales
    # POST - Valida y guarda datos (nombre, CURP, dirección, etc.)
    # Validaciones: CURP, fecha nacimiento, teléfono, dirección
    # Redirige: DOP00005 -> /pago/, otros -> /soliData/
    # Query params: ?dir=dirección_precargada (opcional)
    # Template: di.html
    path('intData/', views.intData, name="data"),

    # Captura de SOLICITUD de trámite con detalles
    # GET - Muestra formulario de solicitud (foto, descripción, ubicación)
    # POST - Procesa solicitud completa con documentos
    # Genera folio automático según PUO
    # Detecta tipo de dispositivo (móvil/tablet/PC) para UI responsiva
    # Template: ds.html
    path('soliData/', views.soliData, name="soli"),

    # Confirmación antes de generar/guardar documento
    # GET - Muestra opciones: guardar en BD o descargar PDF
    # POST - Redirige según action:
    #   - DOP00005: 'guardar' -> /clear/, 'descargar' -> /document2/
    #   - Otros: 'guardar' -> /save/, 'descargar' -> /nada/
    # Template: dg.html
    path('doc/', views.doc, name="doc"),

    # Lista de documentos adjuntos en sesión actual
    # GET - Muestra documentos SubirDocs del UUID actual
    # POST - Continúa a captura de solicitud
    # Requiere cookie 'uuid'
    # Template: docs.html
    path('docs/', views.docs, name="docs"),

    # Eliminar documento adjunto por ID (AJAX)
    # POST - Elimina SubirDocs by ID si pertenece a sesión UUID actual
    # Returns: JsonResponse {'success': True} o {'error': 'mensaje'}
    # Status codes: 200 (éxito), 405 (método inválido), 500 (error)
    # Requiere: método POST, cookie 'uuid'
    path('dell/<int:id>/', views.dell, name='dell'),

    # Subir documento adjunto individual
    # GET - Muestra formulario de subida
    # POST - Guarda archivo en SubirDocs
    # Form fields: ffile (archivo), descp (descripción)
    # Soporta AJAX: retorna JsonResponse si X-Requested-With: XMLHttpRequest
    # Template: docs2.html
    path('docs2/', views.docs2, name="docs2"),

    # Limpiar sesión de trabajo
    # GET - Elimina cookie 'uuid' y redirige al menú
    # No elimina datos de BD, solo termina sesión temporal
    # Uso: Al finalizar un trámite completamente
    path('clear/', views.clear, name="clear"),

    # Captura de pago para licitaciones (DOP00005)
    # GET - Muestra formulario con licitaciones activas
    # POST - Guarda datos de pago y redirige a /doc/
    # Actualiza automáticamente licitaciones vencidas (activa=False)
    # Form fields: fecha, pfm (forma de pago)
    # Template: pago.html
    path('pago/', views.pago, name="pago"),

    # Documento PDF específico para pagos de licitación
    # GET - Genera comprobante de pago en PDF (inline)
    # Solo para trámite DOP00005
    # Content-Type: application/pdf
    # Template renderizado: documet/document2.html
    path('document2/', views.document2, name="document2"),

    # Guardar documento PDF en base de datos
    # GET - Genera PDF y lo guarda en modelo Files
    # Procesa documentos temporales en base64 desde POST
    # Crea registro en Files asociado a solicitud
    # Naming: VS_{asunto}_{nombre}_{apellido}.pdf
    # Template: documet/save.html (confirmación)
    path('save/', views.save_document, name="saveD1"),

    # ============================================================================
    # SERVICIOS DE GEOLOCALIZACIÓN
    # ============================================================================

    # Geocodificación: dirección → coordenadas
    # POST - Convierte dirección de texto a lat/lng
    # Request body: {'address': str}
    # Response: {'success': bool, 'result': {...}, 'processing_time': float}
    # Usa LocalGISService para búsqueda en datos locales
    # Incluye sugerencias si no encuentra resultado exacto
    # @csrf_exempt, solo método POST
    path('geocode/', views.geocode_view, name="geocode"),

    # Geocodificación inversa: coordenadas → dirección
    # POST - Convierte lat/lng a dirección de texto
    # Request body: {'lat': float, 'lng': float}
    # Response: {'success': bool, 'result': {...}, 'processing_time': float}
    # Valida rango de coordenadas para Chihuahua
    # @csrf_exempt, solo método POST
    path('reverse-geocode/', views.reverse_geocode_view, name='reverse_geocode'),

    # ============================================================================
    # ENDPOINTS AJAX AUXILIARES
    # ============================================================================

    # Obtener detalles de licitación por ID (AJAX)
    # POST - Retorna datos de licitación específica
    # Request body: {'licitacion_ID': int}
    # Response: {'codigo': str, 'descripcion': str, 'fecha': str}
    # Status codes: 200 (encontrada), 400 (no existe)
    # Solo método POST
    path('get_licitaciones/', views.get_licitaciones, name='get_licitaciones'),

    # Alias duplicado de get_licitaciones (considerar eliminar)
    # POST - Misma funcionalidad que get_licitaciones/
    path('licitaciones/', views.get_licitaciones, name='licitaciones')

    # Router de APIs REST (comentado hasta implementar FilesViewSet)
    # path('', include(router.urls)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Servir archivos de media en desarrollo (imágenes, PDFs, documentos subidos)
# En producción, esto debería manejarse por nginx u otro servidor web
