
from django.contrib import admin
from django.urls import path
from desUr import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('nada/<uuid:uuid>/', views.document, name="document"),
    path('nav/', views.nav),
    path('', views.home, name="home"),
    path('intData/<uuid:uuid>/', views.intData, name="data"),
    path('soliData/<uuid:uuid>/', views.soliData, name="soli"),
    #path('soliData/', views.soliData, name="soli"),
    path('doc/<uuid:uuid>/', views.doc, name="doc"),
    path('adv/', views.adv, name="adv"),
    path('map/<uuid:uuid>/', views.mapa, name="map"),
    path('docs/<uuid:uuid>/', views.docs, name="docs"),
    path('dell/<uuid:uuid>/<int:id>/', views.dell, name='dell'),
    path('docs2/<uuid:uuid>/', views.docs2, name="docs2"),
]
