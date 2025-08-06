from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('desUr/', include('portaldu.desUr.urls')),
    path('cmin/', include('portaldu.cmin.urls')),
    path('verification/', include('verify_email.urls')),
]

handler404 = 'portaldu.cmin.views.custom_handler404'

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
