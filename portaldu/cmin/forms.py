from django import forms
from django.forms import ModelForm

from .models import Users


class UsersRender(forms.ModelForm):
     password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))
     confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

     class Meta:
          model = Users
          fields = ['email', 'first_name', 'last_name', 'username', 'bday', 'password']
          widgets = {
               'email': forms.EmailInput(attrs={'class':'formcontrol'}),
               'first_name': forms.TextInput(attrs={'class':'formcontrol'}),
               'last_name': forms.TextInput(attrs={'class':'formcontrol'}),
               'username': forms.TextInput(attrs={'class':'formcontrol'}),
               'bday': forms.TextInput(attrs={'type':'text', 'class':'formcontrol'}),
          }


     def clean(self):
          cleaned_data = super().clean()
          password = cleaned_data.get('password')
          confirmP = cleaned_data.get("confirmP")

          if password != confirmP:
               self.add_error('confirmP',"Las contraseñas no coinciden")

     def save(self, commit=True):
          user = super().save(commit=False)
          user.set_password(self.cleaned_data["password"])

          if commit:
               user.save()
          return user


class Login(forms.Form):
     usuario = forms.CharField(widget=forms.TextInput(attrs={'class':'formcontrol'}))
     contrasena = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

