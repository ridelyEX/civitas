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

        if creator_user:
            if not creator_user.is_superuser:

                self.fields['is_superuser'].widget.attrs['disabled'] = True
                self.fields['is_superuser'].initial = False

            if not creator_user.can_manage_users():
                self.fields['is_staff'].widget.attrs['disabled'] = True
                self.fields['is_superuser'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password != confirmP:
            self.add_error('confirmP',"Las contraseñas no coinciden")

        if self.creator_user:
            is_staff = cleaned_data.get('is_staff', False)
            is_superuser = cleaned_data.get('is_superuser', False)

            if not self.creator_user.can_create_user_type(is_staff, is_superuser):
                user_type = "superusuario" if is_superuser else "staff" if is_staff else "invitado"
                raise forms.ValidationError(f"No tienes permisos para crear un {user_type}")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])

        if self.creator_user and self.creator_user.is_superuser:
            user.is_staff = True
            user.is_superuser = False
        elif self.creator_user and self.creator_user.is_staff:
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
