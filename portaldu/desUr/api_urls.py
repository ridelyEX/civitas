from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Router para ViewSets
router = DefaultRouter()
router.register(r'ciudadanos', api_views.CiudadanoViewSet, basename='ciudadano')

urlpatterns = [
    # URLs del router (CRUD completo)
    path('', include(router.urls)),

    # URLs de autenticación
    path('login/', api_views.api_login, name='api-login'),
    path('logout/', api_views.api_logout, name='api-logout'),
    path('profile/', api_views.api_profile, name='api-profile'),

    # URLs personalizadas para ciudadanos
    path('ciudadanos/uuid/<uuid:uuid>/', api_views.ciudadano_por_uuid, name='ciudadano-por-uuid'),
    path('ciudadanos/curp/<str:curp>/', api_views.ciudadano_por_curp, name='ciudadano-por-curp'),
    path('ciudadanos/validar-curp/', api_views.validar_curp, name='validar-curp'),
]
