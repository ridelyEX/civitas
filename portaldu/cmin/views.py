from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from .models import LoginDate, Users


def master(request):
    return render(request, 'master.html')

def users_render(request):
    if request.method == 'POST':
        form = Users(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UsersRender()
    return render(request, 'users.html', {'form':form})


def login_view(request):
    form = Login(request.POST)

    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']
        user = authenticate(request, username=usuario, password=contrasena)
        if user is not None:
            print(user)
            login(request, user)
            LoginDate.objects.create(user_FK=user)
            return redirect('tablas')
        else:
            return HttpResponse("no jalo padre")

    return render(request, 'login.html', {'form':form})

def logout_view(request):
    logout(request)
    return redirect('login')

#@login_required
def tables(request):
    return render(request, 'tables.html')
# Create your views here.
