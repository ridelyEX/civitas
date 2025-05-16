
from django.contrib import admin
from django.urls import path
from desUr import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('nada/', views.document, name="document"),
    path('nav/', views.nav),
    path('', views.home, name="home"),
    path('intData/', views.intData, name="data"),
    path('soliData/', views.soliData, name="soli"),
    #path('soliData/', views.soliData, name="soli"),
    path('doc/', views.doc, name="doc"),
    path('adv/', views.adv, name="adv"),
    path('map/', views.mapa, name="map"),
    path('docs/', views.docs, name="docs"),
    path('dell/<int:id>/', views.dell, name='dell'),
    path('docs2/', views.docs2, name="docs2"),
    path('clear/', views.clear, name="clear"),
    path('pago/', views.pago, name="pago"),
]
