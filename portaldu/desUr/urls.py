from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'files', views.FilesViewSet, basename='files')

urlpatterns = [
    # URLs de autenticación
    path('auth/login/', views.desur_login_view, name='desur_login'),
    path('auth/signin/', views.desur_users_render, name='desur_users'),
    path('auth/logout/', views.desur_logout_view, name='desur_logout'),
    path('auth/user_conf/', views.desur_user_conf, name='desur_user_conf'),
    path('auth/menu/', views.desur_menu, name='desur_menu'),

    # URLs para historial de trámites
    path('auth/historial/', views.desur_historial, name='desur_historial'),
    path('auth/buscar/', views.desur_buscar_tramite, name='desur_buscar'),

    # URLs existentes de desUr
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