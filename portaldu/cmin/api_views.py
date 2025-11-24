"""
API Views del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema de APIs REST para integración con aplicaciones móviles

Este módulo contiene los ViewSets y endpoints de la API REST del sistema
CIVITAS - CMIN, especializado en la recepción y procesamiento de encuestas
desde aplicaciones móviles en modo offline.

Características principales:
- API REST para aplicaciones móviles
- Sincronización de datos offline
- Validación automática con serializers
- Logging detallado para debugging
- Generación automática de UUIDs únicos
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
import uuid
import logging

# Importar modelos y serializers específicos para encuestas móviles
from portaldu.cmin.models import EncuestasOffline, EncuestasOnline, SolicitudesEnviadas
from portaldu.cmin.serializers import OfflineSerializer, OnlineSerializer, SolicitudSerializer

# Logger para seguimiento de eventos y errores de la API
logger = logging.getLogger(__name__)

class AgeoMobileViewSet(viewsets.ViewSet):
    """
    ViewSet especializado para la aplicación móvil de encuestas AGEO.

    Proporciona endpoints para la sincronización de encuestas realizadas
    en dispositivos móviles cuando no hay conexión a internet disponible.

    Funcionalidades principales:
    - Recepción de encuestas desde dispositivos móviles offline
    - Procesamiento de datos en formato JSON, multipart y form
    - Generación automática de UUIDs únicos para evitar duplicados
    - Validación automática de datos recibidos
    - Respuestas estructuradas para la aplicación móvil
    - Logging detallado para debugging y monitoreo
    """

    # Parsers soportados para manejar diferentes tipos de contenido desde la app móvil
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def recibir_encuesta_offline(self, request):
        """
        Endpoint principal para recibir encuestas realizadas en modo offline.

        Este endpoint permite a la aplicación móvil sincronizar encuestas
        que fueron completadas cuando no había conexión a internet disponible.
        Se encarga de validar, procesar y almacenar los datos recibidos.

        Args:
            request (Request): Objeto de solicitud REST que contiene:
                - datos_encuesta (JSON): Información completa de la encuesta
                - latitud (Decimal, opcional): Coordenada de latitud del dispositivo
                - longitud (Decimal, opcional): Coordenada de longitud del dispositivo
                - f_uuid (String): UUID del dispositivo (se regenera en servidor)

        Returns:
            Response: Respuesta JSON con el estado de la operación y datos relevantes

        HTTP Status Codes:
            201: Encuesta creada exitosamente
            400: Error de validación en los datos enviados
            500: Error interno del servidor

        Response Format (Éxito):
            {
                "status": "success",
                "message": "Encuesta guardada correctamente",
                "data": {
                    "id": 123,
                    "uuid": "550e8400-e29b-41d4-a716-446655440000"
                }
            }

        Response Format (Error):
            {
                "status": "error",
                "message": "Error de validación",
                "errors": {...}
            }
        """
        try:
            # Logging detallado para debugging - registrar datos recibidos desde la app móvil
            logger.info(f"datos recibidos: {request.data}")
            logger.info(f"datos recibidos: {request.data}")

            # Crear copia de datos para manipulación segura sin afectar el request original
            data_copy = request.data.copy()
            # Remover UUID del cliente ya que se generará uno nuevo en el servidor
            data_copy.pop('f_uuid', None)

            # Validar datos usando el serializer específico para encuestas offline
            serializer = OfflineSerializer(data=request.data)
            if serializer.is_valid():
                # Logging de datos validados correctamente
                logger.info(f"datos validados: {serializer.validated_data}")

                # Generar UUID único en el servidor para evitar conflictos entre dispositivos
                n_uuid = str(uuid.uuid4())

                # Crear nueva encuesta offline en la base de datos con los datos validados
                encuesta = EncuestasOffline.objects.create(
                    f_uuid = n_uuid,  # UUID único generado en servidor
                    **serializer.validated_data  # Datos validados de la encuesta
                )

                # Respuesta exitosa con información de la encuesta creada
                return Response({
                    'status': 'success',
                    'message': 'Encuesta guardada correctamente',
                    'data': {
                        'id': encuesta.encuesta_ID,  # ID único de la encuesta en BD
                        'uuid': encuesta.f_uuid,     # UUID generado para referencia
                    },
                }, status=status.HTTP_201_CREATED)

            else:
                # Logging detallado de errores de validación para debugging
                logger.error(f"Errores de validación: {serializer.errors}")

                # Log individual de cada campo con error para facilitar debugging
                for field, errors in serializer.errors.items():
                    logger.error(f"Error en el campo '{field}': {errors}")

                # Respuesta de error con detalles específicos de validación
                return Response({
                    'status': 'error',
                    'message': 'Error de validación en los datos enviados',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Manejo de errores generales no capturados por validaciones específicas
            logger.error(f"Error inesperado al procesar encuesta offline: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def recibir_encuesta_online(self, request):
        """
        Endpoint para recibir encuestas realizadas en modo online.

        Este endpoint permite a la aplicación móvil enviar encuestas
        en tiempo real cuando hay conexión a internet disponible.

        Args:
            request (Request): Objeto de solicitud REST con datos de la encuesta

        Returns:
            Response: Respuesta JSON con estado de la operación

        HTTP Methods:
            POST: Crear nueva encuesta online

        Permissions:
            AllowAny: Acceso público para aplicaciones móviles
        """
        try:
            # Logging de recepción de encuesta online
            logger.info(f"Encuesta online recibida: {request.data}")

            # Obtener IP del dispositivo para auditoría y seguimiento
            ip_address = self.get_client_ip(request)

            # Validar datos con serializer específico para encuestas online
            serializer = OnlineSerializer(data=request.data)
            if serializer.is_valid():
                # Generar UUID único para la encuesta online
                n_uuid = str(uuid.uuid4())

                # Crear encuesta online con información adicional de conectividad
                encuesta = EncuestasOnline.objects.create(
                    f_uuid=n_uuid,                      # UUID único generado
                    ip_address=ip_address,              # IP del dispositivo para auditoría
                    **serializer.validated_data         # Datos validados de la encuesta
                )

                # Log de éxito con ID de la encuesta creada
                logger.info(f"Encuesta online guardada: ID {encuesta.encuesta_ID}")

                # Respuesta exitosa con datos de la encuesta online creada
                return Response({
                    'status': 'success',
                    'message': 'Encuesta online guardada correctamente',
                    'data': {
                        'id': encuesta.encuesta_ID,                              # ID único en base de datos
                        'uuid': encuesta.f_uuid,                                 # UUID para referencia
                        'fecha_creacion': encuesta.fecha_creacion.isoformat(),   # Timestamp de creación
                    },
                }, status=status.HTTP_201_CREATED)

            else:
                # Logging de errores de validación en encuestas online
                logger.error(f"Errores en encuesta online: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Error de validación en encuesta online',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Manejo de errores generales en encuestas online
            logger.error(f"Error en encuesta online: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def status_sincronizacion(self, request):
        """
        Endpoint para verificar el estado de sincronización.

        Permite a la aplicación móvil verificar estadísticas de sincronización
        y el estado general del servicio de encuestas.

        Returns:
            Response: Estadísticas de encuestas y estado del servicio
        """
        try:
            # Obtener estadísticas totales de encuestas en el sistema
            total_offline = EncuestasOffline.objects.count()    # Total de encuestas offline almacenadas
            total_online = EncuestasOnline.objects.count()      # Total de encuestas online almacenadas

            # Calcular estadísticas de encuestas recientes (últimas 24 horas)
            desde_ayer = timezone.now() - timezone.timedelta(days=1)
            offline_recientes = EncuestasOffline.objects.filter(
                fecha_creacion__gte=desde_ayer      # Filtrar encuestas offline del último día
            ).count()
            online_recientes = EncuestasOnline.objects.filter(
                fecha_creacion__gte=desde_ayer      # Filtrar encuestas online del último día
            ).count()

            # Respuesta con estadísticas completas del servicio
            return Response({
                'status': 'success',
                'service_status': 'active',         # Estado del servicio (activo)
                'statistics': {
                    'total_encuestas_offline': total_offline,      # Total acumulado offline
                    'total_encuestas_online': total_online,        # Total acumulado online
                    'offline_ultimas_24h': offline_recientes,      # Offline recientes
                    'online_ultimas_24h': online_recientes,        # Online recientes
                    'total_general': total_offline + total_online  # Suma total de todas las encuestas
                },
                'timestamp': timezone.now().isoformat()         # Timestamp de la consulta
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Manejo de errores al obtener estadísticas
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al obtener estadísticas',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_client_ip(self, request):
        """
        Obtiene la dirección IP del cliente que realiza la solicitud.

        Este método maneja correctamente las IPs reales considerando
        proxies, load balancers y CDNs que puedan estar en el camino.

        Args:
            request (Request): Objeto de solicitud HTTP

        Returns:
            str: Dirección IP del cliente real
        """
        # Intentar obtener IP real considerando proxies y load balancers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Tomar la primera IP en caso de múltiples proxies en cadena
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # IP directa sin proxies - conexión directa al servidor
            ip = request.META.get('REMOTE_ADDR')

        return ip

class SolicitudesViewSet(viewsets.ReadOnlyModelViewSet):
    """
       ViewSet para consultar solicitudes enviadas con su estado y datos relacionados.

       Proporciona endpoints para consultar el estado de solicitudes y sus documentos
       asociados de DesUr, útil para seguimiento y monitoreo de solicitudes.

       Funcionalidades:
       - Listado de solicitudes con filtros por estado
       - Consulta de solicitud específica por ID
       - Estadísticas de solicitudes por estado
       - Datos relacionados de documentos de DesUr
       """

    queryset = SolicitudesEnviadas.objects.select_related(
        'doc_FK',
        'doc_FK__fuuid',
        'solicitud_FK'
    ).all()
    serializer_class = SolicitudSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Permite filtrar solicitudes por estado usando query params.

        Query Parameters:
            - estado: 'pendiente', 'en_proceso' o 'completado'
            - fecha_desde: Filtrar desde fecha (YYYY-MM-DD)
            - fecha_hasta: Filtrar hasta fecha (YYYY-MM-DD)
        """

        queryset = super().get_queryset()

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')


        if fecha_desde:
            queryset = queryset.filter(fechaEnvio__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fechaEnvio__date__lte=fecha_hasta)

        return queryset.order_by('-fechaEnvio')

    @action(detail=False, methods=['get'])
    def estado(self, request, estado=None):
        """
        Endpoint para listar solicitudes por estado específico.

        Args:
            Estado de la solicitud ('pendiente', 'en_proceso', 'completado')
        """

        try:
            estado = request.query_params.get('estado')

            if not estado or estado not in ['pendiente', 'en_proceso', 'completado']:
                return Response({
                    'status': 'error',
                    'message': 'Estado inválido. Usar: pendiente, en_proceso, completado.'
                }, status=status.HTTP_400_BAD_REQUEST)

            solicitudes = self.get_queryset().filter(estado=estado)
            serializer = self.get_serializer(solicitudes, many=True)

            return Response({
                'status': 'success',
                'estado': estado,
                'total': solicitudes.count(),
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error al filtrar por estado: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al filtrar solicitudes por estado',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class EncuestasViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión administrativa de encuestas.

    Proporciona endpoints para que los administradores puedan consultar,
    filtrar y gestionar las encuestas recibidas desde aplicaciones móviles.

    Funcionalidades administrativas:
    - Listado de encuestas con filtros avanzados
    - Búsqueda por fechas, ubicación, etc.
    - Exportación de datos a Excel para análisis
    - Estadísticas detalladas para reportes
    - Paginación para manejo eficiente de grandes volúmenes
    """

    @action(detail=False, methods=['get'])
    def listar_offline(self, request):
        """
        Lista todas las encuestas offline con filtros opcionales.

        Permite a los administradores consultar y filtrar las encuestas
        recibidas desde dispositivos móviles en modo offline.

        Query Parameters:
            - fecha_desde (date): Filtrar desde fecha específica (YYYY-MM-DD)
            - fecha_hasta (date): Filtrar hasta fecha específica (YYYY-MM-DD)
            - limit (int): Límite de resultados por página (default: 100)
            - offset (int): Offset para paginación (default: 0)

        Returns:
            Response: Lista paginada de encuestas offline con metadatos
        """
        try:
            # Obtener queryset base ordenado por fecha de creación descendente
            queryset = EncuestasOffline.objects.all().order_by('-fecha_creacion')

            # Aplicar filtros opcionales de fecha si están presentes
            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')

            if fecha_desde:
                # Filtrar encuestas desde la fecha especificada
                queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
            if fecha_hasta:
                # Filtrar encuestas hasta la fecha especificada
                queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)

            # Configurar paginación para manejo eficiente de grandes volúmenes
            limit = int(request.query_params.get('limit', 100))     # Límite por página
            offset = int(request.query_params.get('offset', 0))     # Desplazamiento

            total = queryset.count()                                # Total de registros que cumplen filtros
            encuestas = queryset[offset:offset + limit]             # Slice del queryset para la página actual

            # Serializar datos manualmente para respuesta optimizada
            data = []
            for encuesta in encuestas:
                data.append({
                    'id': encuesta.encuesta_ID,                                            # ID único de la encuesta
                    'uuid': encuesta.f_uuid,                                               # UUID de referencia
                    'fecha_creacion': encuesta.fecha_creacion.isoformat(),                 # Fecha en formato ISO
                    'datos_encuesta': encuesta.datos_encuesta,                             # Datos JSON de la encuesta
                    'latitud': float(encuesta.latitud) if encuesta.latitud else None,     # Coordenada latitud (convertida a float)
                    'longitud': float(encuesta.longitud) if encuesta.longitud else None,  # Coordenada longitud (convertida a float)
                })

            # Respuesta con datos paginados y metadatos de navegación
            return Response({
                'status': 'success',
                'data': data,                           # Datos de la página actual
                'pagination': {
                    'total': total,                     # Total de registros
                    'limit': limit,                     # Límite por página
                    'offset': offset,                   # Desplazamiento actual
                    'has_next': offset + limit < total  # Indicador si hay más páginas
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Manejo de errores en listado de encuestas offline
            logger.error(f"Error al listar encuestas offline: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al obtener encuestas offline',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def exportar_excel(self, request):
        """
        Exporta encuestas a formato Excel para análisis administrativo.

        Genera un archivo Excel con las encuestas filtradas por los criterios
        especificados, permitiendo análisis offline de los datos recopilados.

        Request Body:
            - tipo (str): 'offline' o 'online' o 'ambos' (tipo de encuestas a exportar)
            - fecha_desde (date): Fecha inicio del rango de exportación
            - fecha_hasta (date): Fecha fin del rango de exportación

        Returns:
            HttpResponse: Archivo Excel descargable con los datos solicitados
        """
        try:
            # Importar pandas para manejo de datos y creación de Excel
            import pandas as pd
            from django.http import HttpResponse

            # Obtener parámetros del request para filtrado
            tipo = request.data.get('tipo', 'ambos')        # Tipo de encuestas a exportar
            fecha_desde = request.data.get('fecha_desde')   # Fecha inicio del rango
            fecha_hasta = request.data.get('fecha_hasta')   # Fecha fin del rango

            # Lista para acumular datos de exportación
            data_export = []

            # Procesar encuestas offline si están incluidas en el tipo
            if tipo in ['offline', 'ambos']:
                queryset_offline = EncuestasOffline.objects.all()

                # Aplicar filtros de fecha si están especificados
                if fecha_desde:
                    queryset_offline = queryset_offline.filter(fecha_creacion__date__gte=fecha_desde)
                if fecha_hasta:
                    queryset_offline = queryset_offline.filter(fecha_creacion__date__lte=fecha_hasta)

                # Agregar datos de encuestas offline al export
                for encuesta in queryset_offline:
                    data_export.append({
                        'ID': encuesta.encuesta_ID,                        # ID único de la encuesta
                        'Tipo': 'Offline',                                 # Tipo de encuesta para identificación
                        'UUID': encuesta.f_uuid,                           # UUID de referencia
                        'Fecha': encuesta.fecha_creacion,                  # Fecha de creación
                        'Latitud': encuesta.latitud,                       # Coordenada de latitud
                        'Longitud': encuesta.longitud,                     # Coordenada de longitud
                        'Datos': str(encuesta.datos_encuesta)              # Datos de la encuesta como string
                    })

            # Procesar encuestas online si están incluidas en el tipo
            if tipo in ['online', 'ambos']:
                queryset_online = EncuestasOnline.objects.all()

                # Aplicar filtros de fecha si están especificados
                if fecha_desde:
                    queryset_online = queryset_online.filter(fecha_creacion__date__gte=fecha_desde)
                if fecha_hasta:
                    queryset_online = queryset_online.filter(fecha_creacion__date__lte=fecha_hasta)

                # Agregar datos de encuestas online al export
                for encuesta in queryset_online:
                    data_export.append({
                        'ID': encuesta.encuesta_ID,                        # ID único de la encuesta
                        'Tipo': 'Online',                                  # Tipo de encuesta para identificación
                        'UUID': encuesta.f_uuid,                           # UUID de referencia
                        'Fecha': encuesta.fecha_creacion,                  # Fecha de creación
                        'IP': encuesta.ip_address,                         # Dirección IP del dispositivo
                        'Datos': str(encuesta.datos_encuesta)              # Datos de la encuesta como string
                    })

            # Crear DataFrame de pandas con los datos acumulados
            df = pd.DataFrame(data_export)

            # Configurar respuesta HTTP para descarga de archivo Excel
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="encuestas_export.xlsx"'

            # Escribir DataFrame a Excel y enviarlo como respuesta
            df.to_excel(response, index=False, engine='openpyxl')

            return response

        except Exception as e:
            # Manejo de errores en exportación a Excel
            logger.error(f"Error al exportar encuestas: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al exportar encuestas',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
