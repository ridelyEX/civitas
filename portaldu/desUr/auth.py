"""
Sistema de autenticación unificado para DesUr
Backend de autenticación que funciona exclusivamente con el modelo Users de CMIN
"""
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

logger = logging.getLogger(__name__)
User = get_user_model()

class DesUrAuthBackend(BaseBackend):
    """
    Backend de autenticación unificado que usa exclusivamente el modelo Users de CMIN
    Incluye validaciones específicas para acceso a DesUr basadas en roles
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usuarios usando únicamente el modelo unificado Users
        Valida permisos específicos para DesUr basados en roles
        """
        if not username or not password:
            return None

        try:
            # Autenticar con el modelo unificado Users
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_active:
                # Validar que el usuario tenga acceso a DesUr según su rol
                if hasattr(user, 'has_desur_access') and user.has_desur_access():
                    logger.info(f"Usuario {username} autenticado exitosamente en DesUr")
                    return user
                else:
                    logger.warning(f"Usuario {username} sin permisos de DesUr (rol: {user.rol})")
                    return None
        except User.DoesNotExist:
            logger.warning(f"Usuario {username} no encontrado en el sistema")

        return None

    def get_user(self, user_id):
        """Obtiene un usuario por ID del modelo unificado"""
        try:
            user = User.objects.get(pk=user_id)
            # Validar que el usuario siga teniendo acceso a DesUr
            if hasattr(user, 'has_desur_access') and user.has_desur_access():
                return user
            return None
        except User.DoesNotExist:
            return None

class DesUrUserMiddleware:
    """
    Middleware para manejar usuarios en el sistema DesUr
    Agrega métodos de compatibilidad y validaciones específicas
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar la solicitud antes de la vista
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._ensure_desur_compatibility(request.user)
        
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesa la vista y verifica compatibilidad de usuarios para DesUr
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Asegurar que el usuario tenga todos los métodos necesarios para DesUr
            if not self._has_desur_methods(request.user):
                logger.warning(f"Usuario {request.user.username} sin métodos completos de DesUr")
                # Agregar métodos faltantes dinámicamente si es necesario
                self._add_missing_methods(request.user)

        return None

    def _ensure_desur_compatibility(self, user):
        """
        Asegura que el usuario tenga compatibilidad completa con DesUr
        """
        if not hasattr(user, 'get_full_name'):
            # Agregar método get_full_name si no existe
            user.get_full_name = lambda: f"{user.first_name} {user.last_name}".strip()
        
        if not hasattr(user, 'get_short_name'):
            # Agregar método get_short_name si no existe
            user.get_short_name = lambda: user.first_name

    def _has_desur_methods(self, user):
        """
        Verifica que el usuario tenga todos los métodos necesarios para DesUr
        """
        required_methods = ['has_desur_access', 'get_full_name', 'get_short_name']
        return all(hasattr(user, method) for method in required_methods)

    def _add_missing_methods(self, user):
        """
        Agrega métodos faltantes dinámicamente al usuario
        """
        if not hasattr(user, 'get_full_name'):
            user.get_full_name = lambda: f"{user.first_name} {user.last_name}".strip()
        
        if not hasattr(user, 'get_short_name'):
            user.get_short_name = lambda: user.first_name or user.username

def validate_desur_access(user):
    """
    Función utilitaria para validar acceso específico a DesUr
    """
    if not user.is_authenticated:
        return False, "Usuario no autenticado"
    
    if not hasattr(user, 'has_desur_access'):
        return False, "Usuario sin métodos de DesUr"
    
    if not user.has_desur_access():
        return False, f"Rol '{user.rol}' sin acceso a DesUr"
    
    if not user.is_active:
        return False, "Usuario inactivo"
    
    return True, "Acceso válido"

def get_user_permissions_summary(user):
    """
    Obtiene un resumen de permisos del usuario para debugging
    """
    if not user.is_authenticated:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "username": user.username,
        "rol": getattr(user, 'rol', 'sin_rol'),
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "has_cmin_access": getattr(user, 'has_cmin_access', lambda: False)(),
        "has_desur_access": getattr(user, 'has_desur_access', lambda: False)(),
        "can_access_tables": getattr(user, 'can_access_tables', lambda: False)(),
        "can_create_users": getattr(user, 'can_create_users', lambda: False)(),
    }