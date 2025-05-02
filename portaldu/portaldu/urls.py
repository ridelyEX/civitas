"""
URL configuration for portaldu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from desUr import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nada', views.base, name="nada"),
    path('nav/', views.nav),
    path('', views.home, name="home"),
    path('intData/', views.intData, name="data"),
    path('soliData/', views.soliData, name="soli"),
    path('doc/', views.doc, name="doc"),
    path('adv/', views.adv, name="adv"),
    path('map/', views.mapa, name="map"),

    
]
