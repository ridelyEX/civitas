from rest_framework import serializers
from .models import EncuestasOffline, EncuestasOnline

class OfflineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncuestasOffline
        fields = '__all__'

class OnlienSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncuestasOnline
        fields = '__all__'

class EncuestaSerializer(serializers.Serializer):
    class Meta:
        model = EncuestaSerializer
        fields = '__all__'