from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AgeoMobileViewSet

router = DefaultRouter()
router.register(r'ageo_mobile', AgeoMobileViewSet, basename='ageo_mobile')

urlpatterns = [
    path('encuestas/', include(router.urls))
]