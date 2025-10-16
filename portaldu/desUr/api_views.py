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

logger = logging.getLogger(__name__)

#Mañana se rushea gente

class CiudadanoPagination(PageNumberPagination):
    """Paginación personalizada para ciudadanos"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CiudadanosViewSet(viewsets.ModelViewSet):
    queryset = data.objects.all().order_by('-data_ID')
    serializer_class = CiudadanoSerializer
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
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
        try:
            logger.info(f"Datos del ciudadano recibidos: {request.data}")
            data_copy = request.data.copy()

            if 'bDay' in data_copy:
                fecha = data_copy['bDay']
                if isinstance(fecha, str) and '/' in fecha:
                    try:
                        parts = fecha.split('/')
                        if len(parts) == 3:
                            data_copy['bDay'] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    except Exception as e:
                        logger.error(f"Error convirtiendo la fecha: {str(e)}")

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
        try:
            logger.info(f"Datos de la solicitud recibidos: {request.data}")

            data_copy = request.data.copy()

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
        try:
            logger.info(f"Datos del archivo recibidos: {request.data}")

            data_copy = request.data.copy()

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
