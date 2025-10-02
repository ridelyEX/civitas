from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="Civitas API",
      default_version='v1',
      description="API para el sistema de trámites Civitas",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contacto@civitas.gov.mx"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # APIs del proyecto
    path('api/desur/', include('portaldu.desUr.api_urls')),
    path('api/cmin/', include('portaldu.cmin.api_urls')),

    # Apps principales
    path('desur/', include('portaldu.desUr.urls')),
    path('cmin/', include('portaldu.cmin.urls')),
    path('', include('portaldu.desUr.urls')),  # Página principal

    # Documentación de la API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

# Servir archivos media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
