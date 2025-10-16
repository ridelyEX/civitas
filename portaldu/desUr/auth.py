"""
Sistema de autenticación unificado para DesUr
Permite el uso del modelo Users de CMIN para autenticación en DesUr
"""
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from .models import DesUrUsers

logger = logging.getLogger(__name__)
User = get_user_model()

class DesUrAuthBackend(BaseBackend):
    """
    Backend de autenticación personalizado para migrar usuarios de DesUr
    al sistema unificado usando el modelo Users de CMIN
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usuarios verificando primero en el modelo unificado Users,
        y si no existe, migra desde DesUrUsers
        """
        if not username or not password:
            return None

        try:
            # Intentar autenticar con el modelo unificado Users
            user = User.objects.get(username=username)
            if user.check_password(password):
                logger.info(f"Usuario {username} autenticado exitosamente desde modelo unificado")
                return user
        except User.DoesNotExist:
            # Si no existe en Users, intentar migrar desde DesUrUsers
            try:
                desur_user = DesUrUsers.objects.get(username=username)
                if desur_user.check_password(password):
                    # Migrar usuario de DesUr a Users
                    migrated_user = self._migrate_desur_user(desur_user)
                    if migrated_user:
                        logger.info(f"Usuario {username} migrado exitosamente desde DesUr")
                        return migrated_user
            except DesUrUsers.DoesNotExist:
                logger.warning(f"Usuario {username} no encontrado en ningún modelo")
                pass

        return None

    def get_user(self, user_id):
        """Obtiene un usuario por ID del modelo unificado"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _migrate_desur_user(self, desur_user):
        """
        Migra un usuario de DesUrUsers al modelo unificado Users
        """
        try:
            # Verificar si ya existe un usuario con ese email
            existing_user = User.objects.filter(email=desur_user.email).first()
            if existing_user:
                logger.warning(f"Ya existe un usuario con email {desur_user.email}")
                return None

            # Crear usuario en el modelo unificado
            migrated_user = User.objects.create(
                username=desur_user.username,
                email=desur_user.email,
                first_name=desur_user.first_name,
                last_name=desur_user.last_name,
                bday=desur_user.bday,
                foto=desur_user.foto,
                is_active=desur_user.is_active,
                date_joined=desur_user.date_joined,
                last_login=desur_user.last_login,
                rol='campo'  # Los usuarios de DesUr son por defecto de campo
            )

            # Copiar la contraseña hasheada
            migrated_user.password = desur_user.password
            migrated_user.save()

            # Marcar el usuario de DesUr como migrado (opcional)
            # Podrías agregar un campo 'migrated' a DesUrUsers si lo deseas

            logger.info(f"Usuario {desur_user.username} migrado exitosamente")
            return migrated_user

        except Exception as e:
            logger.error(f"Error al migrar usuario {desur_user.username}: {str(e)}")
            return None

class DesUrUserMiddleware:
    """
    Middleware para manejar la transición del sistema de usuarios de DesUr
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar la solicitud antes de la vista
        response = self.get_response(request)

        # Procesar la respuesta después de la vista
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesa la vista y verifica compatibilidad de usuarios
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Asegurar que el usuario tenga todos los métodos necesarios
            if not hasattr(request.user, 'has_desur_access'):
                logger.warning(f"Usuario {request.user.username} no tiene métodos de DesUr")

        return None

def migrate_all_desur_users():
    """
    Función utilitaria para migrar todos los usuarios de DesUr al modelo unificado
    Usar con precaución y preferiblemente en un management command
    """
    migrated_count = 0
    error_count = 0

    for desur_user in DesUrUsers.objects.all():
        try:
            # Verificar si ya existe
            if User.objects.filter(username=desur_user.username).exists():
                logger.info(f"Usuario {desur_user.username} ya existe en modelo unificado")
                continue

            # Migrar usuario
            backend = DesUrAuthBackend()
            migrated_user = backend._migrate_desur_user(desur_user)

            if migrated_user:
                migrated_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Error migrando usuario {desur_user.username}: {str(e)}")
            error_count += 1

    logger.info(f"Migración completada: {migrated_count} usuarios migrados, {error_count} errores")
    return migrated_count, error_count
