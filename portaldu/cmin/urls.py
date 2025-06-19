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
    path('test/', view.test_email, name='test'),
    path('test2/', view.test_wasap, name='test_wasap'),
]