from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from .forms import Users, Login
from .models import LoginDate, users


def master(request):
    return render(request, 'master.html')

def users_render(request):
    if request.method == 'POST':
        form = Users(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = Users()
    return render(request, 'users.html', {'form':form})


def login(request):
    form = Login(request.POST)
    #userid = request.POST.get('id')
    #us = get_object_or_404(users, id=userid)
    #user = users.objects.filter(user_FK=us)
    if request.method == 'POST':
        if form.is_valid():
            fecha = LoginDate()
            fecha.save()
            return HttpResponse("hola mundo de verdad")
    return render(request, 'login.html', {'form':form})

def tables(request):
    return render(request, 'tables.html')
# Create your views here.
