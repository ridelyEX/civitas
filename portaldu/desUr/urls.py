from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'files', views.FilesViewSet, basename='files')

urlpatterns = [
    path('base/', views.base, name='base'),
    path('nada/', views.document, name="document"),
    path('home/', views.home, name="home"),
    path('intData/', views.intData, name="data"),
    path('soliData/', views.soliData, name="soli"),
    path('doc/', views.doc, name="doc"),
    path('docs/', views.docs, name="docs"),
    path('dell/<int:id>/', views.dell, name='dell'),
    path('docs2/', views.docs2, name="docs2"),
    path('clear/', views.clear, name="clear"),
    path('pago/', views.pago, name="pago"),
    path('document2/', views.document2, name="document2"),
    path('save/', views.save_document, name="saveD1"),
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)