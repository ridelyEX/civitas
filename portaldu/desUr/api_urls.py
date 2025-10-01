from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Router para ViewSets
router = DefaultRouter()
router.register(r'ciudadanos', api_views.CiudadanosViewSet, basename='ciudadano')

urlpatterns = [
    # URLs del router (CRUD completo)
    path('', include(router.urls)),

    path('uuid/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-uuid'),
    path('data/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-data'),
    path('soli/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-soli'),
    path('files/', api_views.CiudadanosViewSet.as_view({'post': 'recibir_datos'}), name='api-files'),


    #path('solicitudes/upload-pdf/', api_views.CiudadanosViewSet.)

    # URLs de autenticación
    #path('login/', api_views.api_login, name='api-login'),
    #path('logout/', api_views.api_logout, name='api-logout'),
    #path('profile/', api_views.api_profile, name='api-profile'),

]
