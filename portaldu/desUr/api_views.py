"""
API Views para DesUr - Endpoints REST para gestión de trámites ciudadanos
Proporciona endpoints para crear y consultar ciudadanos, solicitudes y documentos
Utiliza Django REST Framework para serialización y validación
"""
import uuid

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging

from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from .models import data, Uuid, soli, SubirDocs
from .serializers import (
    CiudadanoSerializer,
    SolicitudSerializer,
    DocumentoSerializer,
    UuidSerializer
)
# Usar el sistema unificado de autenticación
from django.contrib.auth.decorators import login_required
from .views import desur_access_required

# Logger para registro de eventos de la API
logger = logging.getLogger(__name__)

class CiudadanoPagination(PageNumberPagination):
    """
    Paginación personalizada para listados de ciudadanos

    Attributes:
        page_size: Cantidad de registros por página por defecto (20)
        page_size_query_param: Parámetro query para personalizar tamaño de página
        max_page_size: Tamaño máximo permitido de página (100)

    Usage:
        GET /api/ciudadanos/?page=2&page_size=50
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CiudadanosViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de ciudadanos via API REST

    Proporciona endpoints CRUD completos más endpoints personalizados para
    recepción de datos desde aplicaciones móviles o servicios externos

    Endpoints:
        - GET /api/ciudadanos/ - Lista paginada de ciudadanos
        - GET /api/ciudadanos/{id}/ - Detalle de un ciudadano
        - POST /api/ciudadanos/ - Crear nuevo ciudadano
        - PUT/PATCH /api/ciudadanos/{id}/ - Actualizar ciudadano
        - DELETE /api/ciudadanos/{id}/ - Eliminar ciudadano
        - POST /api/ciudadanos/recibir_datos/ - Endpoint personalizado multipropósito

    Permissions:
        AllowAny - Actualmente sin restricciones (considerar cambiar en producción)

    Search:
        Soporta búsqueda por nombre, CURP y apellido paterno vía query param 'search'
    """
    queryset = data.objects.all().order_by('-data_ID')
    serializer_class = CiudadanoSerializer
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        """
        Obtiene queryset de ciudadanos con filtrado opcional por búsqueda

        Query Parameters:
            search: Término de búsqueda (busca en nombre, CURP, apellido paterno)

        Returns:
            QuerySet filtrado y ordenado por ID descendente

        Examples:
            GET /api/ciudadanos/?search=Juan
            GET /api/ciudadanos/?search=JUAP850101
        """
        queryset = self.queryset
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(curp__icontains=search) |
                Q(pApe__contains=search)
            )

        return queryset.order_by('-data_ID')


    @action(detail=False, methods=['post'], url_path='recibir_datos')
    def recibir_datos(self, request):
        """
        Endpoint multipropósito para recibir datos desde aplicaciones externas

        Enruta la petición al handler apropiado según la ruta:
        - /uuid/ -> Crear nuevo UUID de sesión
        - /data/ -> Crear/actualizar datos de ciudadano
        - /soli/ -> Crear nueva solicitud de trámite
        - /files/ -> Subir documento adjunto

        Args:
            request: Request con datos en formato JSON o multipart

        Returns:
            Response con resultado de la operación

        Response Format:
            {
                'status': 'success' | 'error',
                'message': str,
                'data': dict (opcional),
                'errors': dict (opcional en caso de error)
            }

        Status Codes:
            - 201: Recurso creado exitosamente
            - 400: Datos inválidos o faltantes
            - 500: Error interno del servidor

        Examples:
            POST /api/ciudadanos/recibir_datos/uuid/
            POST /api/ciudadanos/recibir_datos/data/
        """
        try:
            path = request.path

            if 'uuid' in path:
                return self._handle_uuid(request)
            elif 'data' in path:
                return self._ciudadano(request)
            elif 'soli' in path:
                return self._solicitudes(request)
            elif 'files' in path:
                return self._documentos(request)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Parámetro requerido (data, soli. files)',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error al procesar los datos: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f"Error al procesar los dato: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_uuid(self, request):
        """
        Handler interno para crear nuevos UUID de sesión

        Args:
            request: Request con datos opcionales del UUID

        Request Body:
            {
                "uuid": "uuid-opcional"  # Si no se provee, se genera automáticamente
            }

        Returns:
            Response con UUID creado y su ID primario

        Response Format (Success):
            {
                'status': 'success',
                'message': 'UUID creado',
                'data': {
                    'prime': int,      # ID primario en BD
                    'uuid': str        # UUID string
                }
            }

        Side Effects:
            - Crea nuevo registro en tabla Uuid

        Status Codes:
            - 201: UUID creado exitosamente
            - 400: Datos inválidos
            - 500: Error en servidor
        """
        try:
            logger.info(f"Datos UUID no encontrados: {request.data}")

            serializer = UuidSerializer(data=request.data)
            if serializer.is_valid():
                uuid_obj = serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'UUID creado',
                    'data': {'prime': uuid_obj.prime, 'uuid': str(uuid_obj.uuid)}
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'status': 'error',
                    'message': 'UUID inválido',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error al crear UUID: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _ciudadano(self, request):
        """
        Handler interno para crear o actualizar datos de ciudadanos

        Args:
            request: Request con datos completos del ciudadano

        Request Body:
            {
                "fuuid": str | int,           # UUID de sesión o ID primario
                "nombre": str,                # Nombre del ciudadano
                "pApe": str,                  # Apellido paterno
                "mApe": str,                  # Apellido materno
                "bDay": str,                  # Fecha nacimiento (YYYY-MM-DD o DD/MM/YYYY)
                "tel": str,                   # Teléfono
                "curp": str,                  # CURP
                "sexo": str,                  # Género
                "dirr": str,                  # Dirección completa
                "asunto": str,                # Código del trámite
                "etnia": str (opcional),      # Grupo étnico
                "disc": str (opcional),       # Discapacidad
                "vul": str (opcional)         # Grupo vulnerable
            }

        Returns:
            Response con ID del ciudadano creado/actualizado

        Date Handling:
            Convierte automáticamente fechas en formato DD/MM/YYYY a YYYY-MM-DD

        Response Format (Success):
            {
                'status': 'success',
                'message': 'Datos del ciudadano',
                'data': {'data_ID': int}
            }

        Validation:
            - fuuid debe existir en tabla Uuid
            - Todos los campos obligatorios deben estar presentes
            - Formato de fecha válido

        Status Codes:
            - 201: Ciudadano creado exitosamente
            - 400: Datos inválidos o UUID no encontrado
            - 500: Error en servidor
        """
        try:
            logger.info(f"Datos del ciudadano recibidos: {request.data}")
            data_copy = request.data.copy()

            # Convertir formato de fecha si viene en formato DD/MM/YYYY
            if 'bDay' in data_copy:
                fecha = data_copy['bDay']
                if isinstance(fecha, str) and '/' in fecha:
                    try:
                        parts = fecha.split('/')
                        if len(parts) == 3:
                            data_copy['bDay'] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    except Exception as e:
                        logger.error(f"Error convirtiendo la fecha: {str(e)}")

            # Resolver UUID a ID primario
            fuuid_value = data_copy.get('fuuid')
            if fuuid_value:
                try:
                    if isinstance(fuuid_value, str):
                        uuid_obj = Uuid.objects.get(uuid=fuuid_value)
                    else:
                        uuid_obj = Uuid.objects.get(prime=fuuid_value)
                    data_copy['fuuid'] = uuid_obj.prime
                except Uuid.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': f"UUID no encontrado: {fuuid_value}"
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = CiudadanoSerializer(data=data_copy)

            if serializer.is_valid():
                logger.info(f"Datos validados: {serializer.validated_data}")
                ciudadano = serializer.save()

                return Response({
                    'status': 'success',
                    'message': 'Datos del ciudadano',
                    'data': {'data_ID': ciudadano.data_ID}
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Error de validación: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Datos de ciudadano inválidos',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error al crear ciudadano: {str(e)}")
            return Response({
                'status': 'error',
                'message': f"Error al procesar ciudadano: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _solicitudes(self, request):
        """
        Handler interno para crear solicitudes de trámites

        Args:
            request: Request con datos de la solicitud

        Request Body:
            {
                "data_ID": int,              # ID del ciudadano (obligatorio)
                "dirr": str,                 # Dirección del problema
                "info": str,                 # Información adicional
                "descc": str,                # Descripción detallada
                "foto": file,                # Imagen del problema (opcional)
                "puo": str,                  # Tipo de proceso (OFI, CRC, MEC, etc.)
                "folio": str (opcional)      # Folio (se genera si no se provee)
            }

        Returns:
            Response con ID de la solicitud creada

        Response Format (Success):
            {
                'status': 'success',
                'message': 'Solicitud creada',
                'data': {'soli_ID': int}
            }

        Validation:
            - data_ID debe existir en tabla data (ciudadano)
            - Campos obligatorios deben estar presentes

        Side Effects:
            - Crea nuevo registro en tabla soli
            - Genera folio si no se proporciona

        Status Codes:
            - 201: Solicitud creada exitosamente
            - 400: Datos inválidos o ciudadano no encontrado
            - 500: Error en servidor
        """
        try:
            logger.info(f"Datos de la solicitud recibidos: {request.data}")

            data_copy = request.data.copy()

            # Validar existencia del ciudadano
            data_id = data_copy.get('data_ID')
            if data_id:
                try:
                    ciudadano = data.objects.get(data_ID=data_id)
                    data_copy['data_ID'] = ciudadano.data_ID
                except data.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': f'Ciudadano no encontrado con ID: {data_id}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = SolicitudSerializer(data=data_copy)

            if serializer.is_valid():
                solicitud = serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Solicitud creada',
                    'data': {'soli_ID': solicitud.soli_ID}
                }, status=status.HTTP_201_CREATED)

            else:
                logger.error(f"Errores validando la solicitud: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Datos de la solicitud inválidos',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error al crear solicitud: {str(e)}")
            return Response({
                'status': 'error',
                'message': f"Error al procesar solicitud: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _documentos(self, request):
        """
        Handler interno para subir documentos adjuntos finales

        Args:
            request: Request con archivo y metadatos

        Request Body (multipart/form-data):
            {
                "fuuid": str,                # UUID de sesión (obligatorio)
                "soli_FK": int,              # ID de solicitud asociada
                "nomDoc": str,               # Nombre del documento
                "finalDoc": file             # Archivo PDF del documento final
            }

        Returns:
            Response con ID del documento guardado

        Response Format (Success):
            {
                'status': 'success',
                'message': 'Documento subido',
                'data': {'fDoc_ID': int}
            }

        Validation:
            - fuuid debe existir en tabla Uuid
            - soli_FK debe existir en tabla soli si se proporciona
            - Archivo debe ser válido

        Side Effects:
            - Crea registro en tabla Files
            - Guarda archivo físico en media/documents/

        Status Codes:
            - 201: Documento subido exitosamente
            - 400: Datos inválidos o referencias no encontradas
            - 500: Error en servidor
        """
        try:
            logger.info(f"Datos del archivo recibidos: {request.data}")

            data_copy = request.data.copy()

            # Resolver UUID a ID primario
            fuuid_value = data_copy.get('fuuid')
            if fuuid_value:
                try:
                    uuid_obj = Uuid.objects.get(uuid=fuuid_value)
                    data_copy['fuuid'] = uuid_obj.prime
                except Uuid.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': f'UUID no encontrado: {fuuid_value}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Resolver ID de solicitud
            soli_id = data_copy.get('soli_FK') or data_copy.get('soli_fk')
            if soli_id:
                try:
                    solicitud = soli.objects.get(soli_ID=soli_id)
                    data_copy['soli_FK'] = solicitud.soli_ID
                except soli.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': f'Solicitud no encontrada: {soli_id}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Importar modelos y serializers necesarios
            from .models import Files
            from .serializers import FilesSerializer

            serializer = FilesSerializer(data=data_copy)

            if serializer.is_valid():
                documento = serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Documento subido',
                    'data': {'fDoc_ID': documento.fDoc_ID}
                }, status=status.HTTP_201_CREATED)

            else:
                logger.error(f"Errores validando el documento: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Datos del documento inválidos',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Erro subiendo el documento: {str(e)}")
            return Response({
                'status': 'error',
                'message': f"Error al procesar documento: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
