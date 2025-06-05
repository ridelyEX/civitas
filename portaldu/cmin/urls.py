from . import views as view
from django.urls import path

urlpatterns = [
    path('main/', view.master, name='master'),
    path('signin/', view.users_render, name='users'),
    path('', view.login_view, name='login'),
    path('tables/', view.tables, name='tablas')
]