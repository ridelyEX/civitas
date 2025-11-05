"""
URLs del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Este archivo define todas las rutas disponibles en el sistema CIVITAS - CMIN
para la gestión administrativa de solicitudes ciudadanas.

Funcionalidades principales:
- Autenticación y gestión de usuarios
- Procesamiento de solicitudes ciudadanas
- Seguimiento de trámites administrativos
- Sistema de notificaciones
- Gestión de documentos Excel
- APIs para integración externa
"""

from django.urls import path, include

from . import views as view

urlpatterns = [
    # === RUTAS PRINCIPALES DEL SISTEMA ===

    # Página principal del sistema (dashboard)
    path('main/', view.master, name='master'),

    # === GESTIÓN DE USUARIOS Y AUTENTICACIÓN ===

    # Registro de nuevos funcionarios (solo administradores)
    # Vista: users_render() - Formulario de creación de usuarios con validación de permisos
    path('signin/', view.users_render, name='users'),

    # Login principal del sistema (ruta raíz)
    # Vista: login_view() - Autenticación unificada CMIN/DesUr con migración automática
    path('', view.login_view, name='login'),

    # Cierre de sesión
    # Vista: logout_view() - Termina la sesión y redirige al login
    path('logout/', view.logout_view, name='logout'),

    # Configuración de perfil personal
    # Vista: user_conf() - Permite actualizar datos personales, foto y contraseña
    path('user_conf/', view.user_conf, name='user_conf'),

    # === GESTIÓN DE SOLICITUDES ===

    # Panel principal de solicitudes (requiere rol administrador/delegador)
    # Vista: tables() - Muestra solicitudes pendientes y enviadas con filtros
    path('tables/', view.tables, name='tablas'),

    # Guardar solicitud pendiente para procesamiento
    # Vista: save_request() - Convierte documento en solicitud pendiente
    path('save/', view.save_request, name='saveSoli'),

    # Envío de solicitudes por correo electrónico
    # Vista: sendMail() - Envía emails automáticos con documentos adjuntos
    path('send/', view.sendMail, name='send_mail'),

    # === SEGUIMIENTO Y MONITOREO ===

    # Panel de seguimiento de trámites (requiere rol administrador/delegador)
    # Vista: seguimiento() - Monitoreo completo con filtros, estadísticas y gestión de estados
    path('seguimiento/', view.seguimiento, name='seguimiento'),

    # Menú principal del sistema (post-login)
    # Vista: menu() - Dashboard principal con opciones según rol del usuario
    path('menu/', view.menu, name='menu'),

    # === BANDEJA DE ENTRADA ===

    # Bandeja de entrada centralizada de solicitudes
    # Vista: bandeja_entrada() - Lista de solicitudes recibidas con estado y prioridad
    path('bandeja/', view.bandeja_entrada, name='bandeja_entrada'),

    # Actualización de estado de solicitudes via AJAX
    # Vista: actualizar_estado_solicitud() - Cambio de estado sin recargar página
    path('actualizar-estado/', view.actualizar_estado_solicitud, name='actualizar_estado'),

    # === SISTEMA DE NOTIFICACIONES ===

    # Panel de notificaciones del usuario
    # Vista: notifications() - Lista de notificaciones con filtros por estado
    path('notificaciones/', view.notifications, name='notificaciones'),

    # Marcar notificación como leída (AJAX)
    # Vista: marcar_notificacion() - Actualiza estado de notificación específica
    # Parámetro: notificacion_id (int) - ID único de la notificación
    path('marcar-leida/<int:notificacion_id>/', view.marcar_notificacion, name="marcar_notificacion"),

    # === GESTIÓN DE ARCHIVOS EXCEL ===

    # Subida de archivos Excel para licitaciones
    # Vista: subir_excel() - Importación masiva de licitaciones con validación de estructura
    # Columnas requeridas: 'Fecha límite', 'No. licitación', 'Descripción'
    path('excel/', view.subir_excel, name="excel"),

    # Exportación de reportes a Excel
    # Vista: get_excel() - Genera reporte completo con múltiples hojas (ciudadanos, solicitudes, etc.)
    path('importar/', view.get_excel, name="importar_excel"),

    # === APIs PARA INTEGRACIÓN EXTERNA ===

    # Incluye todas las rutas de la API REST
    # Archivo: api_urls.py - Endpoints para aplicaciones móviles y servicios externos
    # Funcionalidades: Recepción de encuestas offline, sincronización de datos
    path('api/', include('portaldu.cmin.api_urls')),
]
#handler404 = 'portaldu.cmin.views.custom_handler404'
