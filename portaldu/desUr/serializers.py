"""
Serializers del módulo DesUr (Desarrollo Urbano)
Sistema de serialización para APIs REST del módulo de trabajo de campo

Este módulo contiene todos los serializers del sistema CIVITAS - DesUr,
utilizados para la validación y serialización de datos de ciudadanos,
solicitudes, documentos y trámites urbanos.

Características principales:
- Serialización de datos de ciudadanos con validaciones CURP
- Gestión de solicitudes y trámites urbanos
- Validación de documentos y archivos subidos
- Integración con sistema de UUIDs para sesiones
- Cálculo automático de campos derivados (edad, nombre completo)
"""

from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import Files, data, Uuid, soli, SubirDocs

class FilesSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Files (archivos/documentos finales del sistema).

    Maneja la serialización y validación de documentos PDF finales generados
    por el sistema, incluyendo validaciones de UUID y referencias a solicitudes.

    Funcionalidades:
    - Validación automática de todos los campos del modelo Files
    - Conversión y validación de UUIDs de string a objetos Uuid
    - Validación de referencias a solicitudes existentes
    - Manejo de archivos PDF y documentos oficiales

    Fields:
        - fDoc_ID: ID único del documento
        - nomDoc: Nombre del documento
        - finalDoc: Archivo PDF del documento final
        - fuuid: UUID de sesión asociado
        - soli_FK: Solicitud asociada (opcional)
    """

    class Meta:
        model = Files          # Modelo Django asociado para archivos finales
        fields = '__all__'     # Incluir todos los campos del modelo

    def validate(self, attrs):
        """
        Validaciones personalizadas para el serializer de archivos.

        Valida que los UUIDs y referencias a solicitudes sean correctos
        antes de crear o actualizar registros de archivos.

        Args:
            attrs (dict): Atributos del archivo a validar

        Returns:
            dict: Atributos validados y convertidos

        Raises:
            ValidationError: Si UUID o solicitud no son válidos
        """
        # Validar y convertir UUID de string a objeto Uuid si es necesario
        fuuid = attrs.get('fuuid')
        if fuuid and not isinstance(fuuid, Uuid):
            try:
                # Buscar objeto Uuid por campo 'prime' (ID primario)
                attrs['fuuid'] = Uuid.objects.get(prime=fuuid)
            except Uuid.DoesNotExist:
                raise serializers.ValidationError('UUID no válido')

            # Validar referencia a solicitud si está presente
            soli_fk = attrs.get('soli_FK')
            if soli_fk and not isinstance(soli_fk, soli):
                try:
                    # Buscar solicitud por ID
                    attrs['soli_FK'] = soli.objects.get(soli_ID=soli_fk)
                except soli.DoesNotExist:
                    raise serializers.ValidationError("Solicitud no válida")

            return attrs

class UuidSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Uuid (identificadores únicos de sesión).

    Maneja la serialización de UUIDs utilizados para identificar
    sesiones de usuario y vincular datos relacionados durante el
    proceso de captura de trámites.

    Funcionalidades:
    - Serialización de identificadores únicos
    - Validación de formato UUID
    - Gestión de sesiones de usuario

    Fields:
        - prime: ID primario autoincremental
        - uuid: String UUID único (generado automáticamente)
    """

    class Meta:
        model = Uuid           # Modelo Django asociado para UUIDs
        fields = '__all__'     # Incluir todos los campos del modelo

class CiudadanoSerializer(serializers.ModelSerializer):
    """
    Serializer principal para datos de ciudadanos.

    Maneja la serialización y validación completa de información ciudadana,
    incluyendo validaciones específicas de CURP mexicana y cálculos automáticos
    de campos derivados como edad y nombre completo.

    Funcionalidades:
    - Validación de CURP con expresión regular específica mexicana
    - Cálculo automático de edad basado en fecha de nacimiento
    - Generación de nombre completo concatenado
    - Validaciones de unicidad y formato de datos
    - Integración con sistema de UUIDs de sesión
    - Normalización automática de CURP a mayúsculas

    Fields:
        - data_ID: ID único del ciudadano (autoincremental)
        - fuuid: UUID de sesión (read-only, asignado automáticamente)
        - nombre: Nombre(s) del ciudadano
        - pApe: Apellido paterno
        - mApe: Apellido materno
        - bDay: Fecha de nacimiento (YYYY-MM-DD)
        - asunto: Código del trámite solicitado
        - tel: Teléfono de contacto (10-15 dígitos)
        - curp: CURP validada (18 caracteres, formato oficial)
        - sexo: Género (valores: 'hombre', 'mujer', 'H', 'M')
        - dirr: Dirección completa del ciudadano
        - disc: Información sobre discapacidad (opcional)
        - etnia: Pertenencia a grupo étnico (opcional)
        - vul: Pertenencia a grupo vulnerable (opcional)
        - edad: Campo calculado - edad actual en años
        - nombre_completo: Campo calculado - nombre y apellidos concatenados
    """

    # Campo UUID de solo lectura (se asigna automáticamente en el backend)
    fuuid = UuidSerializer(read_only=True)

    # Campos calculados automáticamente mediante métodos get_*
    edad = serializers.SerializerMethodField()              # Edad calculada desde fecha nacimiento
    nombre_completo = serializers.SerializerMethodField()   # Nombre + apellidos concatenados

    # Validador personalizado para CURP mexicana
    # Formato oficial: 4 letras + 6 dígitos + H/M + 5 letras + 1 dígito/letra + 1 dígito
    # Ejemplo válido: JUAP850101HDFRRR09
    curp_validator = RegexValidator(
        regex=r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$',
        message='CURP debe tener el formato correcto (18 caracteres)'
    )

    # Campo CURP con validación automática de formato
    curp = serializers.CharField(validators=[curp_validator])

    class Meta:
        model = data           # Modelo Django asociado para datos ciudadanos
        fields = [
            'data_ID',         # ID único del ciudadano (PK)
            'fuuid',           # UUID de sesión (FK a Uuid)
            'nombre',          # Nombre(s) del ciudadano
            'pApe',            # Apellido paterno
            'mApe',            # Apellido materno
            'bDay',            # Fecha de nacimiento
            'asunto',          # Asunto/motivo de la solicitud (código DOP)
            'tel',             # Teléfono de contacto
            'curp',            # CURP (Clave Única de Registro de Población)
            'sexo',            # Género (H/M)
            'dirr',            # Dirección completa
            'disc',            # Información de discapacidad
            'etnia',           # Pertenencia étnica
            'vul',             # Grupo vulnerable
            'edad',            # Campo calculado - edad actual
            'nombre_completo'  # Campo calculado - nombre completo
        ]

    def get_edad(self, obj):
        """
        Calcula la edad actual del ciudadano basada en su fecha de nacimiento.

        Considera si el cumpleaños ya pasó en el año actual para calcular
        la edad correctamente.

        Args:
            obj (data): Instancia del modelo data (ciudadano)

        Returns:
            int: Edad en años completos
            None: Si no hay fecha de nacimiento registrada

        Example:
            Si nació 01/01/1990 y hoy es 15/06/2025 -> retorna 35
            Si nació 01/01/1990 y hoy es 01/01/2025 -> retorna 35
            Si nació 15/12/1990 y hoy es 01/01/2025 -> retorna 34 (aún no cumple años)
        """
        if obj.bDay:
            from datetime import date
            today = date.today()
            # Calcular edad considerando si ya pasó el cumpleaños este año
            return today.year - obj.bDay.year - ((today.month, today.day) < (obj.bDay.month, obj.bDay.day))
        return None

    def get_nombre_completo(self, obj):
        """
        Genera el nombre completo concatenando nombre y apellidos.

        Formatea correctamente eliminando espacios extras.

        Args:
            obj (data): Instancia del modelo data (ciudadano)

        Returns:
            str: Nombre completo formateado y limpio (sin espacios extras)

        Example:
            nombre="Juan Carlos", pApe="Pérez", mApe="García"
            -> "Juan Carlos Pérez García"
        """
        return f"{obj.nombre} {obj.pApe} {obj.mApe}".strip()

    def validate_curp(self, value):
        """
        Validación adicional para el campo CURP.

        Verifica que la CURP no esté duplicada en el sistema,
        permitiendo actualización del mismo registro pero evitando
        duplicados entre diferentes ciudadanos.

        Args:
            value (str): Valor de CURP a validar

        Returns:
            str: CURP en mayúsculas y validada

        Raises:
            ValidationError: Si la CURP ya existe para otro ciudadano diferente

        Business Rules:
            - CURP debe ser única en el sistema
            - Se normaliza automáticamente a mayúsculas
            - Se permite actualizar el mismo registro sin error
        """
        if data.objects.filter(curp=value).exists():
            # Permitir actualización del mismo registro
            if self.instance and self.instance.curp == value:
                return value
            raise serializers.ValidationError("Ya existe un ciudadano con esta CURP")
        return value.upper()  # Convertir a mayúsculas para consistencia

    def validate(self, attrs):
        """
        Validaciones generales y cruzadas del serializer de ciudadanos.

        Realiza validaciones de integridad de datos que requieren
        múltiples campos o lógica compleja.

        Args:
            attrs (dict): Diccionario con todos los atributos a validar

        Returns:
            dict: Atributos validados y potencialmente normalizados

        Raises:
            ValidationError: Si alguna validación cruzada falla

        Validations:
            - Normalización de campos de texto a mayúsculas
            - Validación de coherencia entre campos
            - Conversión de UUID si es necesario
        """
        # Normalizar nombre y apellidos a mayúsculas
        if 'nombre' in attrs:
            attrs['nombre'] = attrs['nombre'].upper()
        if 'pApe' in attrs:
            attrs['pApe'] = attrs['pApe'].upper()
        if 'mApe' in attrs:
            attrs['mApe'] = attrs['mApe'].upper()

        # Validar y convertir UUID si viene como ID
        fuuid = attrs.get('fuuid')
        if fuuid and not isinstance(fuuid, Uuid):
            try:
                attrs['fuuid'] = Uuid.objects.get(prime=fuuid)
            except Uuid.DoesNotExist:
                raise serializers.ValidationError({'fuuid': 'UUID no válido'})

        return attrs

class SolicitudSerializer(serializers.ModelSerializer):
    """
    Serializer para solicitudes de trámites ciudadanos.

    Maneja la serialización y validación de solicitudes de trámites
    de obra pública y desarrollo urbano, incluyendo fotografías,
    descripciones y generación automática de folios.

    Funcionalidades:
    - Validación de datos de solicitud
    - Manejo de imágenes adjuntas (fotos del problema)
    - Generación automática de folios si no se proporcionan
    - Validación de tipo de proceso (PUO)
    - Asociación con ciudadanos existentes
    - Registro de empleado que procesa la solicitud

    Fields:
        - soli_ID: ID único de la solicitud (PK)
        - data_ID: Ciudadano que realiza la solicitud (FK)
        - dirr: Dirección específica del problema/solicitud
        - info: Información adicional proporcionada
        - descc: Descripción detallada del problema
        - foto: Imagen del problema (campo de archivo)
        - puo: Tipo de proceso/origen de la solicitud
        - folio: Folio único generado (formato: GOP-XXX-#####-XXXX/YY)
        - fecha: Fecha y hora de creación (auto)
        - processed_by: Empleado que procesó la solicitud (FK)
    """

    # Nombre del usuario que procesó la solicitud (campo derivado)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)

    class Meta:
        model = soli           # Modelo Django asociado para solicitudes
        fields = [
            'soli_ID',         # ID único de la solicitud
            'data_ID',         # Datos del ciudadano (objeto completo)
            'doc_ID',          # Documento asociado
            'processed_by',    # Usuario que procesó (ID)
            'processed_by_name', # Nombre del usuario que procesó
            'dirr',            # Dirección específica del trámite
            'calle',           # Calle específica
            'colonia',         # Colonia/barrio
            'cp',              # Código postal
            'descc',           # Descripción detallada del trámite
            'fecha',           # Fecha de creación de la solicitud
            'info',            # Información adicional
            'puo',             # Punto de Ubicación Oficial
            'foto',            # Fotografía adjunta
            'folio'            # Número de folio oficial
        ]


class DocumentoSerializer(serializers.ModelSerializer):
    """
    Serializer para documentos adjuntos temporales (SubirDocs).

    Maneja la serialización y validación de documentos que los ciudadanos
    adjuntan como evidencia o complemento a sus solicitudes durante
    el proceso de captura.

    Funcionalidades:
    - Validación de archivos adjuntos
    - Validación de descripciones y nombres de documentos
    - Integración con sistema de UUIDs
    - Validación de tamaño y tipo de archivos

    Fields:
        - sdoc_ID: ID único del documento (PK)
        - fuuid: UUID de sesión asociado (FK)
        - nomDoc: Nombre del archivo
        - descDoc: Descripción del contenido del documento
        - doc: Archivo adjunto (PDF, imagen, etc.)
    """

    class Meta:
        model = SubirDocs      # Modelo Django asociado para documentos temporales
        fields = '__all__'     # Incluir todos los campos del modelo

    def validate_doc(self, value):
        """
        Valida el archivo adjunto (tamaño, tipo, etc.).

        Args:
            value (File): Archivo a validar

        Returns:
            File: Archivo validado

        Raises:
            ValidationError: Si el archivo no cumple los requisitos
        """
        # Validar tamaño máximo (5 MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("El archivo no puede superar 5 MB")

        return value

    def validate(self, attrs):
        """
        Validaciones generales del serializer de documentos.

        Args:
            attrs (dict): Atributos del documento a validar

        Returns:
            dict: Atributos validados
        """
        # Validar y convertir UUID si es necesario
        fuuid = attrs.get('fuuid')
        if fuuid and not isinstance(fuuid, Uuid):
            try:
                attrs['fuuid'] = Uuid.objects.get(prime=fuuid)
            except Uuid.DoesNotExist:
                raise serializers.ValidationError({'fuuid': 'UUID no válido'})

        return attrs
