from django import forms

from portaldu.cmin.models import Users  # Importar el modelo Users de cmin
from .models import (PpCS, PpEscuela, PpGeneral, PpPluvial, PpParque, PpInfraestructura, DesUrUsers)

# Usar el modelo de usuario de cmin

CHOICES_STATE = [
    ("bueno", "Bueno"),
    ("regular", "Regular"),
    ("malo", "Malo"),
]

class DesUrUsersRender(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

    class Meta:
        model = DesUrUsers  # Cambiar a usar el modelo Users de cmin
        fields = ['email', 'first_name', 'last_name','username', 'bday','password', 'foto']
        widgets = {
          'email': forms.EmailInput(attrs={'class':'formcontrol'}),
          'first_name': forms.TextInput(attrs={'class':'formcontrol'}),
          'last_name': forms.TextInput(attrs={'class':'formcontrol'}),
          'username': forms.TextInput(attrs={'class':'formcontrol'}),
          'bday': forms.DateInput(attrs={'class':'formcontrol', 'type':'date'}),
          'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password != confirmP:
            self.add_error('confirmP',"Las contraseñas no coinciden")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class DesUrLogin(forms.Form):
     usuario = forms.CharField(widget=forms.TextInput(attrs={'class':'sign'}))
     contrasena = forms.CharField(widget=forms.PasswordInput(attrs={'class':'sign'}))


class DesUrUsersConfig(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)

    class Meta:
        model = DesUrUsers  # Cambiar a usar el modelo Users de cmin
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


class GeneralRender(forms.ModelForm):

    cfe = forms.ChoiceField(   
        choices=[('','-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="Instalación CFE",
    )

    agua = forms.ChoiceField(
        choices=[('', '-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="Instalación agua potable",
    )
    drenaje = forms.ChoiceField(
        choices=[('','-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="Instalación drenaje",
    )
    impermeabilizacion = forms.ChoiceField(
        choices=[('','-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="Impermeabilización",
    )
    climas = forms.ChoiceField(
        choices=[('','-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="climas",
    )
    alumbrado = forms.ChoiceField(
        choices=[('', '-----')] + PpGeneral.CHOICES_STATE,
        required=False,
        widget=forms.RadioSelect(),
        label="alumbrado",
    )

    # Campo personalizado para teléfono
    telefono = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '6441234567',
            'pattern': '[0-9]{10}',
            'title': 'Ingresa 10 dígitos sin espacios'
        }),
        help_text="Formato: 10 dígitos sin espacios ni guiones"
    )

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Remover espacios, guiones y paréntesis
            telefono_limpio = ''.join(filter(str.isdigit, telefono))

            # Validar que tenga exactamente 10 dígitos
            if len(telefono_limpio) != 10:
                raise forms.ValidationError("El teléfono debe tener exactamente 10 dígitos")

            # Validar que inicie con 6 (para Chihuahua) - opcional
            if not telefono_limpio.startswith('6'):
                raise forms.ValidationError("El teléfono debe iniciar con 6")

            return telefono_limpio
        return telefono

    class Meta:
        model = PpGeneral
        exclude = ['pp_ID', 'fecha_pp', 'calle_p', 'colonia_p', 'cp_p', 'fuuid']

        widgets = {
            'nombre_promovente':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre del promovente'}),
            'categoria':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Categoría del proyecto'}),
            'direccion_proyecto':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Dirección del proyecto'}),
            'desc_p':forms.Textarea(attrs={'class':'form-control', 'placeholder':'Descripción del proyecto'}),
            'notas_importantes':forms.Textarea(attrs={'class':'form-control', 'placeholder':'Notas importantes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.instalation_choices:
            for instalacion, estado in self.instance.instalation_choices.items():
                if instalacion in self.fields:
                    self.fields[instalacion].initial = estado

    def save(self, commit=True):
        instance = super().save(commit=False)
        instalation_choices = {}
        instalaciones = ['cfe', 'agua', 'drenaje', 'impermeabilizacion', 'climas', 'alumbrado']
        for instalacion in instalaciones:
            estado = self.cleaned_data.get(instalacion)
            if estado:
                instalation_choices[instalacion] = estado
        instance.instalation_choices = instalation_choices
        if commit:
            instance.save()
        print(self.cleaned_data)
        return instance


class ParqueRender(forms.ModelForm):

    class Meta:
        model = PpParque
        exclude = ['p_parque_ID', 'fk_pp']

        widgets = {
            'cancha_futbol_rapido':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'cancha_futbol_soccer': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'cancha_futbol_7x7': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'cancha_beisbol': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'cancha_softbol': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'cancha_usos_multiples': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'cancha_otro': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'alumbrado_rehabilitacion': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'alumbrado_nuevo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'juegos_dog_park': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'juegos_infantiles': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'juegos_ejercitadores': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'juegos_otros': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'techumbre_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'techumbre_kiosko': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'equipamiento_botes': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'equipamiento_bancas': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'equipamiento_andadores': forms.CheckboxInput(
              attrs={'class': 'check-form-control'}),
            'equipamiento_rampas': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'notas_parque':forms.Textarea(attrs={'class':'text-form-control'}),
        }

class EscuelaRender(forms.ModelForm):
    class Meta:
        model = PpEscuela
        exclude = ['p_escuela_ID', 'fk_pp']

        widgets = {
            'nom_escuela':forms.TextInput(attrs={'class':'form-control'}),
            'rehabilitacion_baños':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'rehabilitacion_salones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_electricidad': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'rehabilitacion_gimnasio': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_otro': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'contruccion_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_aula': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'cancha_futbol_rapido': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'cancha_futbol_soccer': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'cancha_futbol_7x7': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'notas_escuela': forms.Textarea(attrs={'class': 'text-form-control'}),
        }

class CsRender(forms.ModelForm):
    class Meta:
        model = PpCS
        exclude = ['p_cs_ID', 'fk_pp']

        widgets = {
            'rehabilitacion_baños': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_salones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_electricidad': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_gimnasio': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'contruccion_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_salon': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_otro': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),
        }

class InfraestructuraRender(forms.ModelForm):
    class Meta:
        model = PpInfraestructura
        exclude = ['pp_infraestructura_id', 'fk_pp']

        widgets = {
            'infraestructura_barda':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'infraestructura_baquetas': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_muo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_camellon': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_crucero': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_ordenamiento': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_er': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_mejora': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_peatonal': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_bayoneta': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_topes': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'infraestructura_puente': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pavimentacion_asfalto': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'paviemntacion_rehabilitacion': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'señalamiento_pintura': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'señalamiento_señales': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),

        }

class PluvialRender(forms.ModelForm):
    class Meta:
        model = PpPluvial
        exclude = ['pp_pluvial_ID', 'fk_pp']


        widgets = {
            'pluvial_muro_contencion':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'pluvial_canaliazacion': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_puente_peatonal': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_vado': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_puente': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_desalojo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_rejillas': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_lavaderos': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_obra_hidraulica': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_reposicion_piso': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_proteccion_inundaciones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),

        }

#Excel

class UploadExcel(forms.Form):
    file = forms.FileField(
        label='Selecciona un archivo Excel',
        help_text='El archivo debe ser en formato .xlsx',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.endswith('.xlsx') or not file.name.endswith('.xls') or not file.name.endswith('.xlsm') or not file.name.endswith('.xlsb'):
            raise forms.ValidationError("El archivo debe ser en formato .xlsx, .xls, .xlsm o .xlsb")
        return file
