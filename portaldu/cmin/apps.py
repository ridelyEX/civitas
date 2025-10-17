"""
Configuración de la aplicación CMIN (Centro de Monitoreo Integral de Notificaciones)

Este módulo define la configuración principal de la aplicación CMIN
dentro del proyecto Django CIVITAS, estableciendo las configuraciones
básicas y metadatos de la aplicación.
"""

from django.apps import AppConfig


class CminConfig(AppConfig):
    """
    Clase de configuración para la aplicación CMIN.

    Define las configuraciones básicas de la aplicación Django,
    incluyendo el tipo de campo automático por defecto,
    el nombre de la aplicación y el nombre legible.

    Características:
    - Configuración de campos de clave primaria automáticos
    - Definición del nombre interno de la aplicación
    - Nombre legible para interfaces administrativas
    - Configuración de señales y hooks de la aplicación
    """

    # Tipo de campo automático por defecto para claves primarias
    # BigAutoField permite IDs hasta 9,223,372,036,854,775,807
    default_auto_field = 'django.db.models.BigAutoField'

    # Nombre interno de la aplicación (ruta completa del módulo)
    # Utilizado por Django para identificar la aplicación en el proyecto
    name = 'portaldu.cmin'

    # Nombre legible de la aplicación para interfaces administrativas
    # Aparece en el panel de administración de Django
    verbose_name = 'CMIN - Centro de Monitoreo Integral de Notificaciones'
