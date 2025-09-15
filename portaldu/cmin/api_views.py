from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
import uuid
import logging

from portaldu.cmin.models import EncuestasOffline, EncuestasOnline
from portaldu.cmin.serializers import OfflineSerializer, OnlineSerializer
logger = logging.getLogger(__name__)

class AgeoMobileViewSet(viewsets.ViewSet):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def recibir_encuesta_offline(self, request):
        try:
            logger.info(f"datos recibidos: {request.data}")
            logger.info(f"datos recibidos: {request.data}")

            data_copy = request.data.copy()
            data_copy.pop('f_uuid', None)

            serializer = OfflineSerializer(data=request.data)
            if serializer.is_valid():
                logger.info(f"datos validados: {serializer.validated_data}")

                n_uuid = str(uuid.uuid4())
                encuesta = EncuestasOffline.objects.create(
                    f_uuid = n_uuid,
                    **serializer.validated_data
                )

                return Response({
                    'status': 'success',
                    'message': 'Encuesta guardada correctamente',
                    'data': {
                        'id': encuesta.encuesta_ID,
                        'uuid': encuesta.f_uuid,
                    },
                }, status=status.HTTP_201_CREATED)

            else:
                logger.error(f"Errores de validación: {serializer.errors}")

                for field, errors in serializer.error.items():
                    logger.error(f"Error en el campo '{field}': {errors}")
                return Response({
                    'status': 'error',
                    'message': 'Encuesta inválida',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"error comleto: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Error al procesar la encuesta: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def recibir_encuesta_online(self, request):
        try:
            serializer = OnlineSerializer(data=request.data)
            if serializer.is_valid():

                n_uuid = str(uuid.uuid4())
                encuesta = EncuestasOnline.objects.create(
                    f_uuid = n_uuid,
                    **serializer.validated_data
                )

                return Response({
                    'status': 'success',
                    'message': 'Encuesta guardada correctamente',
                    'data': {
                        'id': encuesta.encuesta_ID,
                        'uuid': encuesta.f_uuid,
                    },
                }, status=status.HTTP_201_CREATED)

            else:
                return Response({
                    'status': 'error',
                    'message': 'Encuesta inválida',
                    'errors': serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al procesar la encuesta: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

