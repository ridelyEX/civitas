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
    #Bandeja de entrada
    path('bandeja/', view.bandeja_entrada, name='bandeja_entrada'),
    path('actualizar-estado/', view.actualizar_estado_solicitud, name='actualizar_estado'),
    #Notificaciones
    path('notificaciones/', view.notifications, name='notificaciones'),
    path('marcar-leida/<int:notificacion_id>/', view.marcar_notificacion, name="marcar_notificacion"),
    # excel
    path('excel/', view.subir_excel, name="excel"),
    path('importar/', view.get_excel, name="importar_excel")
]

