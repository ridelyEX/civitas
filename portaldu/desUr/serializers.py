from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import Files, data, Uuid, soli, SubirDocs

class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'

class UuidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uuid
        fields = '__all__'
        read_only_fields = ['uuid']

class CiudadanoSerializer(serializers.ModelSerializer):
    """Serializer para datos de ciudadanos"""
    fuuid = UuidSerializer(read_only=True)
    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()

    # Validadores personalizados
    curp_validator = RegexValidator(
        regex=r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$',
        message='CURP debe tener el formato correcto (18 caracteres)'
    )

    curp = serializers.CharField(validators=[curp_validator])

    class Meta:
        model = data
        fields = [
            'data_ID', 'fuuid', 'nombre', 'pApe', 'mApe', 'bDay',
            'asunto', 'tel', 'curp', 'sexo', 'dirr', 'disc',
            'etnia', 'vul', 'edad', 'nombre_completo'
        ]
        read_only_fields = ['data_ID']

    def get_edad(self, obj):
        """Calcular edad del ciudadano"""
        if obj.bDay:
            from datetime import date
            today = date.today()
            return today.year - obj.bDay.year - ((today.month, today.day) < (obj.bDay.month, obj.bDay.day))
        return None

    def get_nombre_completo(self, obj):
        """Obtener nombre completo"""
        return f"{obj.nombre} {obj.pApe} {obj.mApe}".strip()

    def validate_curp(self, value):
        """Validación adicional para CURP"""
        if data.objects.filter(curp=value).exists():
            # Permitir actualización del mismo registro
            if self.instance and self.instance.curp == value:
                return value
            raise serializers.ValidationError("Ya existe un ciudadano con esta CURP")
        return value.upper()

    def validate(self, attrs):
        """Validaciones generales"""
        # Validar que el nombre no esté vacío
        if not attrs.get('nombre', '').strip():
            raise serializers.ValidationError({"nombre": "El nombre es obligatorio"})

        # Validar fecha de nacimiento
        if attrs.get('bDay'):
            from datetime import date
            if attrs['bDay'] > date.today():
                raise serializers.ValidationError({"bDay": "La fecha de nacimiento no puede ser futura"})

        return attrs

class CiudadanoCreateSerializer(CiudadanoSerializer):
    """Serializer específico para crear ciudadanos"""
    uuid_session = serializers.UUIDField(write_only=True, required=True)

    class Meta(CiudadanoSerializer.Meta):
        fields = CiudadanoSerializer.Meta.fields + ['uuid_session']

    def create(self, validated_data):
        """Crear ciudadano con UUID de sesión"""
        uuid_session = validated_data.pop('uuid_session')

        try:
            uuid_obj = Uuid.objects.get(uuid=uuid_session)
        except Uuid.DoesNotExist:
            raise serializers.ValidationError({"uuid_session": "UUID de sesión no válido"})

        validated_data['fuuid'] = uuid_obj
        return super().create(validated_data)

class SolicitudSerializer(serializers.ModelSerializer):
    """Serializer para solicitudes de trámites"""
    data_ID = CiudadanoSerializer(read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)

    class Meta:
        model = soli
        fields = [
            'soli_ID', 'data_ID', 'doc_ID', 'processed_by', 'processed_by_name',
            'dirr', 'calle', 'colonia', 'cp', 'descc', 'fecha', 'info',
            'puo', 'foto', 'folio'
        ]
        read_only_fields = ['soli_ID', 'fecha', 'folio']

class DocumentoSerializer(serializers.ModelSerializer):
    """Serializer para documentos subidos"""
    fuuid = UuidSerializer(read_only=True)

    class Meta:
        model = SubirDocs
        fields = '__all__'
        read_only_fields = ['doc_ID', 'fechaDoc']
