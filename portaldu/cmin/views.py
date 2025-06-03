from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django import forms

from .forms import Users, Login

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
    if request.method == 'POST':
        form = Login(request.POST)
        if form.is_valid():
            return HttpResponse("hola mundo de verdad")
    return render(request, 'login.html')
# Create your views here.
