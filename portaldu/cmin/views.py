from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from .forms import Users, Login
from .models import LoginDate


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
    if request.method == 'POST':
        if form.is_valid():
            fecha = LoginDate()
            fecha.save()
            return HttpResponse("hola mundo de verdad")
    return render(request, 'login.html',{'form':form})
# Create your views here.
