from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
import uuid

from portaldu.cmin.models import EncuestasOffline, EncuestasOnline
from portaldu.cmin.serializers import OfflineSerializer, OnlineSerializer


class AgeoMobileViewSet(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'])
    def recibir_encuesta_offline(self, request):
        try:
            serializer = OfflineSerializer(data=request.data)
            if serializer.is_valid():

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

