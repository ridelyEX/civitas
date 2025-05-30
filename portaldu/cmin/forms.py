from django import forms
from django.forms import ModelForm

from .models import users

class Users(ModelForm):
     class Meta:
          model = users
          exclude = ['user_ID']

