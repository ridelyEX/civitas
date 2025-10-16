from django import forms
from django.forms import ModelForm
from .models import Users

class UsersRender(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

    class Meta:
        model = Users
        fields = ['email', 'first_name', 'last_name','username', 'bday','password', 'foto', 'rol', 'is_staff', 'is_superuser']
        widgets = {
            'email': forms.EmailInput(attrs={'class':'formcontrol'}),
            'first_name': forms.TextInput(attrs={'class':'formcontrol'}),
            'last_name': forms.TextInput(attrs={'class':'formcontrol'}),
            'username': forms.TextInput(attrs={'class':'formcontrol'}),
            'bday': forms.DateInput(attrs={'class':'formcontrol', 'type':'date'}),
            'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
            'rol': forms.Select(attrs={'class':'formcontrol'}),
        }

    def __init__(self, *args, creator_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creator_user = creator_user

        # Controlar qué roles puede crear según el rol del creador
        if self.creator_user is None or self.creator_user.rol != 'administrador':
            # Solo administradores pueden crear otros administradores
            self.fields['rol'].choices = [
                ('delegador', 'Delegador'),
                ('campo', 'Campo'),
            ]
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

        # Validar permisos de rol
        if self.creator_user:
            rol = cleaned_data.get('rol')
            if rol == 'administrador' and self.creator_user.rol != 'administrador':
                self.add_error('rol', "Solo administradores pueden crear otros administradores")

            is_staff = cleaned_data.get('is_staff', False)
            is_superuser = cleaned_data.get('is_superuser', False)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # CORREGIR: Usar set_password para encriptar la contraseña
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])

        if self.creator_user is None:
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True

        # Configurar permisos según el rol
        rol = user.rol
        if rol == 'administrador':
            user.is_staff = True
            user.is_superuser = True
        elif rol == 'delegador':
            user.is_staff = True
            user.is_superuser = False
        else:  # campo
            user.is_staff = False
            user.is_superuser = False

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
        fields = ['username', 'foto', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class':'formcontrol'}),
            'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
            'rol': forms.Select(attrs={'class':'formcontrol'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['foto'].required = False
        self.fields['rol'].required = False

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

        # Actualizar permisos según el nuevo rol
        rol = user.rol
        if rol == 'administrador':
            user.is_staff = True
            user.is_superuser = True
        elif rol == 'delegador':
            user.is_staff = True
            user.is_superuser = False
        else:  # campo
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
        return user

#Excel
class UploadExcel(forms.Form):
    file = forms.FileField()
