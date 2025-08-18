from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.views.static import serve
from django.http import HttpResponse
import os

# Función para servir el Service Worker
def serve_sw(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/javascript')
        response['Cache-Control'] = 'no-cache'
        response['Service-Worker-Allowed'] = '/'
        return response
    except FileNotFoundError:
        return HttpResponse('Service Worker not found', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ageo/', include('portaldu.desUr.urls')),  # Cambiado de vuelta a 'ageo/'
    path('cmin/', include('portaldu.cmin.urls')),

    # Servir Service Worker desde la raíz y desde static
    path('sw.js', serve_sw, name='service_worker_root'),
    path('static/sw.js', serve_sw, name='service_worker_static'),
]

handler404 = 'portaldu.cmin.views.custom_handler404'

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
