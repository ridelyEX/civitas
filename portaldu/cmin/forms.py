from django import forms
from django.forms import ModelForm
from .models import Users

class UsersRender(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

    class Meta:
        model = Users
        fields = ['email', 'first_name', 'last_name','username', 'bday','password', 'foto', 'is_staff', 'is_superuser']
        widgets = {
            'email': forms.EmailInput(attrs={'class':'formcontrol'}),
            'first_name': forms.TextInput(attrs={'class':'formcontrol'}),
            'last_name': forms.TextInput(attrs={'class':'formcontrol'}),
            'username': forms.TextInput(attrs={'class':'formcontrol'}),
            'bday': forms.DateInput(attrs={'class':'formcontrol', 'type':'date'}),
            'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
        }

    def __init__(self, *args, creator_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creator_user = creator_user

        if self.creator_user is None:
            self.fields.pop('is_staff', None)
            self.fields.pop('is_superuser', None)
            self.fields.pop('groups', None)
            self.fields.pop('user_permissions', None)


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password != confirmP:
            self.add_error('confirmP',"Las contraseñas no coinciden")

        if self.creator_user:
            is_staff = cleaned_data.get('is_staff', False)
            is_superuser = cleaned_data.get('is_superuser', False)


        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.creator_user is None:
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True

        if commit:
            user.save()
        return user



class Login(forms.Form):
     usuario = forms.CharField(widget=forms.TextInput(attrs={'class':'sign'}))
     contrasena = forms.CharField(widget=forms.PasswordInput(attrs={'class':'sign'}))


class UsersConfig(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)

    class Meta:
        model = Users
        fields = ['username', 'foto']
        widgets = {
            'username': forms.TextInput(attrs={'class':'formcontrol'}),
            'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['foto'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password:
             if password != confirmP:
                 self.add_error('confirmP',"Las contraseñas no coinciden")
        elif confirmP:
             self.add_error('password', "La contraseña no puede estar vacía")
        return cleaned_data


    def save(self, commit=True):
        user = super().save(commit=False)

        if self.cleaned_data.get("password"):
          user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user

#Excel
class UploadExcel(forms.Form):
    file = forms.FileField()
