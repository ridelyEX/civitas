from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Comentar el router hasta que se implemente FilesViewSet
# router = DefaultRouter()
# router.register(r'files', views.FilesViewSet, basename='files')

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

    # URLs presupuesto particicpativo
    path('pp/general', views.gen_render, name='general'),
    path('pp/escuelas', views.escuela_render, name='escuelas'),
    path('pp/parques', views.parque_render, name='parques'),
    path('pp/centros', views.cs_render, name='centros'),
    path('pp/infraestructura', views.infraestructura_render, name='infraestructura'),
    path('pp/pluviales', views.pluvial_render, name='pluviales'),
    path('pp/document', views.pp_document, name='pp_document' ),

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
    # path('', include(router.urls)),  # Comentar hasta implementar FilesViewSet

    # URLs para PWA y funcionalidad móvil
    path('sw.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
    path('offline/', views.offline_page, name='offline'),
    path('install/', views.install_prompt, name='install_prompt'),

    # URLs para móviles
    path('mobile/menu/', views.mobile_menu, name='mobile_menu'),
    path('mobile/historial/', views.mobile_historial, name='mobile_historial'),
    path('mobile/confirmacion/', views.confirmacion_mobile, name='mobile_confirmacion'),

    # APIs para funcionalidad offline
    path('api/sync/', views.sync_offline_data, name='sync_offline_data'),
    path('api/user-data/', views.api_user_data, name='api_user_data'),

    path('get_licitaciones/', views.get_licitaciones, name="get_licitaciones"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)