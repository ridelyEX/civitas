from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django import forms

from .forms import Users
from .models import users

def master(request):
    return render(request, 'master.html')

def usersRender(request):
    context = {}
    userForm = Users()
    context['form'] = userForm
    return render(request, 'users.html', context)
# Create your views here.
