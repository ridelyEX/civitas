from . import views as view
from django.urls import path

urlpatterns = [
    path('main/', view.master, name='master'),
    path('signin/', view.users_render, name='users'),
    path('', view.login_view, name='login'),
    path('tables/', view.tables, name='tablas'),
    path('save/', view.save_request, name='saveSoli'),
    path('send/', view.sendMail, name='send_mail'),
    path('logout/', view.logout_view, name='logout'),
    path('user_conf/', view.user_conf, name='user_conf'),
    path('seguimiento/', view.seguimiento, name='seguimiento'),
    path('menu/', view.menu, name='menu'),
    # excel
    path('excel/', view.subir_excel, name="excel"),
]

