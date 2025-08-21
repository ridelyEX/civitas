from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging

from .models import data, Uuid, soli, SubirDocs
from .serializers import (
    CiudadanoSerializer,
    CiudadanoCreateSerializer,
    SolicitudSerializer,
    DocumentoSerializer,
    UuidSerializer
)
from .auth import desur_login_required

logger = logging.getLogger(__name__)

class CiudadanoPagination(PageNumberPagination):
    """Paginación personalizada para ciudadanos"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CiudadanoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para CRUD de ciudadanos

    Endpoints disponibles:
    - GET /api/ciudadanos/ - Listar todos los ciudadanos
    - POST /api/ciudadanos/ - Crear nuevo ciudadano
    - GET /api/ciudadanos/{id}/ - Obtener ciudadano específico
    - PUT /api/ciudadanos/{id}/ - Actualizar ciudadano completo
    - PATCH /api/ciudadanos/{id}/ - Actualizar campos específicos
    - DELETE /api/ciudadanos/{id}/ - Eliminar ciudadano
    """
    queryset = data.objects.all().select_related('fuuid').order_by('-data_ID')
    serializer_class = CiudadanoSerializer
    pagination_class = CiudadanoPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Usar serializer específico para creación"""
        if self.action == 'create':
            return CiudadanoCreateSerializer
        return CiudadanoSerializer

    def get_queryset(self):
        """Filtrar queryset con parámetros de búsqueda"""
        queryset = self.queryset

        # Filtro por nombre
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(
                Q(nombre__icontains=nombre) |
                Q(pApe__icontains=nombre) |
                Q(mApe__icontains=nombre)
            )

        # Filtro por CURP
        curp = self.request.query_params.get('curp', None)
        if curp:
            queryset = queryset.filter(curp__iexact=curp)

        # Filtro por UUID de sesión
        uuid_session = self.request.query_params.get('uuid', None)
        if uuid_session:
            queryset = queryset.filter(fuuid__uuid=uuid_session)

        # Filtro por asunto/trámite
        asunto = self.request.query_params.get('asunto', None)
        if asunto:
            queryset = queryset.filter(asunto__icontains=asunto)

        # Filtro por teléfono
        telefono = self.request.query_params.get('telefono', None)
        if telefono:
            queryset = queryset.filter(tel__icontains=telefono)

        return queryset

    def create(self, request, *args, **kwargs):
        """Crear nuevo ciudadano con validaciones extra"""
        logger.info(f"Creando nuevo ciudadano - Usuario: {request.user.username}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                ciudadano = serializer.save()
                logger.info(f"Ciudadano creado exitosamente - ID: {ciudadano.data_ID}")

                # Serializar con el serializer de lectura para respuesta completa
                response_serializer = CiudadanoSerializer(ciudadano)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            logger.error(f"Error creando ciudadano: {str(e)}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Actualizar ciudadano con logging"""
        ciudadano = self.get_object()
        logger.info(f"Actualizando ciudadano ID: {ciudadano.data_ID} - Usuario: {request.user.username}")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Eliminar ciudadano con validaciones"""
        ciudadano = self.get_object()

        # Verificar si tiene solicitudes asociadas
        if soli.objects.filter(data_ID=ciudadano).exists():
            return Response(
                {"error": "No se puede eliminar el ciudadano porque tiene solicitudes asociadas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Eliminando ciudadano ID: {ciudadano.data_ID} - Usuario: {request.user.username}")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def solicitudes(self, request, pk=None):
        """Obtener todas las solicitudes de un ciudadano"""
        ciudadano = self.get_object()
        solicitudes = soli.objects.filter(data_ID=ciudadano).select_related('processed_by')
        serializer = SolicitudSerializer(solicitudes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        """Obtener todos los documentos de un ciudadano"""
        ciudadano = self.get_object()
        documentos = SubirDocs.objects.filter(fuuid=ciudadano.fuuid)
        serializer = DocumentoSerializer(documentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Búsqueda avanzada de ciudadanos"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Parámetro 'q' es requerido"}, status=400)

        ciudadanos = self.get_queryset().filter(
            Q(nombre__icontains=query) |
            Q(pApe__icontains=query) |
            Q(mApe__icontains=query) |
            Q(curp__icontains=query) |
            Q(tel__icontains=query) |
            Q(dirr__icontains=query)
        )

        page = self.paginate_queryset(ciudadanos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ciudadanos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de ciudadanos"""
        total_ciudadanos = self.get_queryset().count()

        # Estadísticas por género
        por_genero = {}
        for sexo in ['M', 'F', 'Masculino', 'Femenino']:
            count = self.get_queryset().filter(sexo__iexact=sexo).count()
            if count > 0:
                por_genero[sexo] = count

        # Estadísticas por asunto
        from django.db.models import Count
        por_asunto = list(
            self.get_queryset()
            .values('asunto')
            .annotate(count=Count('data_ID'))
            .order_by('-count')[:10]
        )

        # Ciudadanos registrados hoy
        hoy = timezone.now().date()
        # Como no tienes fecha de creación en el modelo, usaremos el ID como aproximación
        ciudadanos_recientes = self.get_queryset().order_by('-data_ID')[:10].count()

        return Response({
            'total_ciudadanos': total_ciudadanos,
            'por_genero': por_genero,
            'por_asunto': por_asunto,
            'registros_recientes': ciudadanos_recientes
        })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ciudadano_por_uuid(request, uuid):
    """
    Obtener ciudadano por UUID de sesión
    GET /api/ciudadanos/uuid/{uuid}/
    """
    try:
        uuid_obj = get_object_or_404(Uuid, uuid=uuid)
        ciudadano = get_object_or_404(data, fuuid=uuid_obj)
        serializer = CiudadanoSerializer(ciudadano)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error obteniendo ciudadano por UUID {uuid}: {str(e)}")
        return Response(
            {"error": "Ciudadano no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ciudadano_por_curp(request, curp):
    """
    Obtener ciudadano por CURP
    GET /api/ciudadanos/curp/{curp}/
    """
    try:
        ciudadano = get_object_or_404(data, curp__iexact=curp)
        serializer = CiudadanoSerializer(ciudadano)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error obteniendo ciudadano por CURP {curp}: {str(e)}")
        return Response(
            {"error": "Ciudadano no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Permitir acceso sin autenticación
def api_login(request):
    """
    Endpoint de login para la API
    POST /api/login/
    Body: {"username": "usuario", "password": "contraseña"}
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            "error": "Username y password son requeridos",
            "code": "MISSING_CREDENTIALS"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Usar el backend de autenticación personalizado
        from .auth import DesUrAuthBackend
        auth_backend = DesUrAuthBackend()
        user = auth_backend.authenticate(request, username=username, password=password)

        if user:
            # Crear sesión
            request.session['desur_user_id'] = user.id
            request.session['desur_username'] = user.username
            request.session.save()

            logger.info(f"Login API exitoso para usuario: {username}")

            return Response({
                "success": True,
                "message": "Login exitoso",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "date_joined": user.date_joined,
                    "last_login": user.last_login
                },
                "session_id": request.session.session_key
            }, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Intento de login API fallido para usuario: {username}")
            return Response({
                "error": "Credenciales inválidas",
                "code": "INVALID_CREDENTIALS"
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        logger.error(f"Error en login API: {str(e)}")
        return Response({
            "error": "Error interno del servidor",
            "code": "INTERNAL_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_logout(request):
    """
    Endpoint de logout para la API
    POST /api/logout/
    """
    try:
        username = getattr(request.user, 'username', 'Unknown')
        request.session.flush()  # Eliminar toda la sesión

        logger.info(f"Logout API exitoso para usuario: {username}")

        return Response({
            "success": True,
            "message": "Logout exitoso"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error en logout API: {str(e)}")
        return Response({
            "error": "Error interno del servidor"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_profile(request):
    """
    Obtener información del usuario autenticado
    GET /api/profile/
    """
    try:
        user = request.user
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "date_joined": user.date_joined,
                "last_login": user.last_login
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error obteniendo perfil API: {str(e)}")
        return Response({
            "error": "Error interno del servidor"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validar_curp(request):
    """
    Validar si una CURP ya existe
    POST /api/ciudadanos/validar-curp/
    Body: {"curp": "CURP123456789012345"}
    """
    curp = request.data.get('curp', '').upper()
    if not curp:
        return Response({"error": "CURP es requerida"}, status=400)

    existe = data.objects.filter(curp=curp).exists()
    return Response({
        "curp": curp,
        "existe": existe,
        "disponible": not existe
    })
