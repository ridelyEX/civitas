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

class CiudadanosViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def recibir_datos(self, request):
        try:
            tipo_param = request.query_params.get('tipo', '').lower()
            logger.info(f"Datos recibidos para {tipo_param}: {request.data}")

            if tipo_param == 'data':
                return self._ciudadano(request)
            elif tipo_param == 'soli':
                return self._solicitudes(request)
            elif tipo_param == 'Files':
                return self._documentos(request)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Parámetro requerido',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error al procesar los datos: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f"Error al procesar los dato: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _ciudadano(self, request):
        data_copy = request.data.copy()
        data_copy.pop("uuid", None)

        serializer = CiudadanoSerializer(data=request.data)

        if serializer.is_valid():
            logger.info(f"Datos validados: {serializer.validated_data}")

            n_uuid = str(uuid.uuid4())
            ciudadano = data.objects.create(
                f_uuid = n_uuid,
                **serializer.validated_data,
            )

            return Response({
                'status': 'success',
                'message': 'Datos del ciudadano',
                'data': {
                    'id': ciudadano.data_ID,
                    'uuid': ciudadano.f_uuid,
                    'tipo': 'ciudadano',
                }
            }, status=status.HTTP_201_CREATED)

        else:
            logger.error(f"Error de validación: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Datos de ciudadano inválidos',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def _solicitudes(self, request):
        serializer = SolicitudSerializer(data=request.data)

        if serializer.is_valid():
            solicitud = soli.objects.create(**serializer.validated_data)
            return Response({
                'status': 'success',
                'message': 'Solicitud creada',
                'data': {
                    'id': solicitud.soli_ID,
                    'tipo': 'solicitud',
                }
            }, status=status.HTTP_201_CREATED)

        else:
            logger.error(f"Errores calidando la solicitud: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Datos de la solicitud inválidos',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def _documentos(self, request):
        serializer = DocumentoSerializer(data=request.data)

        if serializer.is_valid():
            documento = SubirDocs.objects.create(**serializer.validated_data)
            return Response({
                'status': 'success',
                'message': 'Documento subido',
                'data': {
                    'id': documento.doc_ID,
                    'tipo': 'documento',
                }
            }, status=status.HTTP_201_CREATED)

        else:
            logger.error(f"Errores validando el documento: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Datos del documento inválidos',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

