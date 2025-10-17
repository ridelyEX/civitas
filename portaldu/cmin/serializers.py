"""
Serializers del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema de serialización para APIs REST

Este módulo contiene todos los serializers del sistema CIVITAS - CMIN,
utilizados para la validación y serialización de datos en las APIs REST,
especialmente para la integración con aplicaciones móviles de encuestas.

Características principales:
- Serialización de modelos de encuestas offline/online
- Validación automática de datos recibidos desde apps móviles
- Conversión entre formatos JSON y modelos Django
- Soporte para sincronización de datos offline
"""

from rest_framework import serializers
from .models import EncuestasOffline, EncuestasOnline, EncuestaModel


class OfflineSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo EncuestasOffline.

    Maneja la serialización y validación de encuestas recibidas desde
    dispositivos móviles en modo offline (sin conexión a internet).

    Funcionalidades:
    - Validación automática de todos los campos del modelo EncuestasOffline
    - Conversión de datos JSON a instancias de modelo Django
    - Manejo de campos opcionales y nulos
    - Validación de tipos de datos (enteros, strings, etc.)
    - Soporte para datos demográficos y respuestas de encuesta
    """

    class Meta:
        model = EncuestasOffline  # Modelo Django asociado
        fields = '__all__'        # Incluir todos los campos del modelo

        # Campos adicionales que pueden ser útiles para validación personalizada:
        # - f_uuid: UUID único de la encuesta
        # - fecha_respuesta: Fecha de respuesta en formato string
        # - escuela, colonia: Datos de ubicación
        # - rol_social, genero: Datos demográficos
        # - pregunta_1 a pregunta_17: Respuestas de la encuesta
        # - sincronizado, completada: Estados de control


class OnlineSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo EncuestasOnline.

    Maneja la serialización y validación de encuestas realizadas
    directamente online desde dispositivos con conectividad.

    Funcionalidades:
    - Validación de encuestas en tiempo real
    - Serialización de respuestas en formato JSON/texto
    - Validación de referencia a plantilla de encuesta
    - Manejo de ID de usuario y UUID único
    - Control de estado de completitud
    """

    class Meta:
        model = EncuestasOnline   # Modelo Django asociado
        fields = '__all__'        # Incluir todos los campos del modelo

        # Campos principales:
        # - usuario_ID: Identificador del usuario que responde
        # - f_uuid: UUID único para consistencia con sistema offline
        # - fecha_respuesta: Timestamp de la respuesta
        # - completada: Estado de completitud (0/1)
        # - respuestas: Datos de respuestas en formato texto/JSON
        # - encuesta_FK: Referencia a la plantilla de encuesta


class EncuestaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo EncuestaModel.

    Maneja la serialización de plantillas/estructuras de encuestas
    disponibles en el sistema para ser utilizadas por las aplicaciones.

    Funcionalidades:
    - Serialización de definiciones de encuestas
    - Validación de estructura de preguntas
    - Manejo de estado activo/inactivo
    - Conversión de metadatos de encuesta
    - Soporte para configuraciones de encuesta
    """

    class Meta:
        model = EncuestaModel     # Modelo Django asociado
        fields = '__all__'        # Incluir todos los campos del modelo

        # Campos principales:
        # - nombre: Nombre descriptivo de la encuesta
        # - descripcion: Propósito y contexto de la encuesta
        # - fecha_creacion: Timestamp de creación
        # - activa: Estado de disponibilidad (1=activa, 0=inactiva)
        # - preguntas: Estructura de preguntas en formato JSON/texto

