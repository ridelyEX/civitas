from . import views as view
from django.urls import path

urlpatterns = [
    path('main/', view.master, name='master'),
    path('', view.usersRender, name='users')
]