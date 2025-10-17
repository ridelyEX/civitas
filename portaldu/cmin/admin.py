"""
Configuración del panel de administración de Django para el módulo CMIN
(Centro de Monitoreo Integral de Notificaciones)

Este módulo define la configuración del panel administrativo de Django,
registrando los modelos del sistema CIVITAS - CMIN para su gestión
a través de la interfaz web de administración.

Funcionalidades:
- Registro de modelos para gestión administrativa
- Configuración de interfaces de administración personalizadas
- Control de acceso a funciones administrativas
- Herramientas de gestión de datos del sistema
"""

from django.contrib import admin

# Importar modelos específicos del módulo CMIN para registro en admin
from portaldu.cmin.models import Licitaciones

# === REGISTRO DE MODELOS EN EL PANEL DE ADMINISTRACIÓN ===

# Registrar modelo Licitaciones para gestión administrativa
# Permite a los administradores:
# - Crear, editar y eliminar licitaciones
# - Gestionar fechas límite y estados
# - Visualizar licitaciones activas e inactivas
# - Realizar búsquedas y filtros
admin.site.register(Licitaciones)