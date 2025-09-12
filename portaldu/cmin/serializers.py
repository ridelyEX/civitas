from rest_framework import serializers
from .models import EncuestasOffline, EncuestasOnline, EncuestaModel


class OfflineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncuestasOffline
        fields = '__all__'

class OnlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncuestasOnline
        fields = '__all__'

class EncuestaSerializer(serializers.Serializer):
    class Meta:
        model = EncuestaModel
        fields = '__all__'