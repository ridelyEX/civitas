"""
Formularios del módulo DesUr (Desarrollo Urbano)
Sistema de formularios Django para captura de datos de trámites y presupuesto participativo

Este módulo contiene todos los formularios del sistema CIVITAS - DesUr,
utilizados para la validación y renderizado de formularios HTML para:
- Registro y autenticación de usuarios (LEGACY - usar sistema unificado)
- Captura de propuestas de Presupuesto Participativo
- Validación de datos de ciudadanos y proyectos

Características principales:
- Validación automática de campos
- Widgets personalizados con clases CSS de Bootstrap
- Validación de teléfonos (10 dígitos para Chihuahua)
- Manejo de campos JSONField para instalaciones
- Validación de contraseñas con confirmación
- Formularios dinámicos basados en categorías

Categorías de Presupuesto Participativo:
- Parques: Canchas, alumbrado, juegos, techumbres, equipamiento
- Escuelas: Rehabilitación, construcción, canchas deportivas
- Centros Comunitarios: Rehabilitación y construcción de espacios
- Infraestructura: Bardas, banquetas, pavimentación, señalamiento
- Soluciones Pluviales: Muros, canalizaciones, obras hidráulicas
"""

from django import forms

from portaldu.cmin.models import Users  # Importar el modelo Users unificado de CMIN
from .models import (PpCS, PpEscuela, PpGeneral, PpPluvial, PpParque, PpInfraestructura)

# Constante para opciones de estado de instalaciones
# Utilizada en formularios de Presupuesto Participativo
CHOICES_STATE = [
    ("bueno", "Bueno"),       # Instalación en buen estado
    ("regular", "Regular"),   # Instalación funcional pero requiere mantenimiento
    ("malo", "Malo"),         # Instalación en mal estado, requiere rehabilitación
]


class DesUrUsersRender(forms.ModelForm):
    """
    Formulario LEGACY para registro de usuarios de DesUr

    ⚠️ DEPRECADO: Este formulario ya no se usa, el sistema utiliza
    el sistema de autenticación unificado de CMIN.

    Se mantiene por compatibilidad pero debe ser removido en futuras versiones.
    Usar en su lugar el sistema de registro unificado en portaldu.cmin.forms

    Fields:
        - email: Correo electrónico del usuario
        - first_name: Nombre(s) del usuario
        - last_name: Apellidos del usuario
        - username: Nombre de usuario único
        - bday: Fecha de nacimiento
        - password: Contraseña (encriptada)
        - confirmP: Confirmación de contraseña (no se guarda)
        - foto: Fotografía de perfil (opcional)

    Validations:
        - Contraseñas deben coincidir
        - Email debe ser único
        - Username debe ser único

    Security:
        - Password se encripta con set_password() antes de guardar
    """
    # Campo de contraseña con widget de entrada oculta
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))
    # Campo de confirmación de contraseña (no se guarda en BD)
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}))

    class Meta:
        model = Users  # Usar el modelo Users unificado de CMIN
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
        """
        Validación personalizada para verificar que las contraseñas coincidan

        Returns:
            dict: Datos limpiados y validados

        Raises:
            ValidationError: Si las contraseñas no coinciden
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password != confirmP:
            self.add_error('confirmP',"Las contraseñas no coinciden")

    def save(self, commit=True):
        """
        Guarda el usuario con la contraseña encriptada

        Args:
            commit (bool): Si True, guarda inmediatamente en BD

        Returns:
            Users: Instancia del usuario creado

        Security:
            Usa set_password() para encriptar la contraseña con hash seguro
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class DesUrLogin(forms.Form):
    """
    Formulario LEGACY de login para DesUr

    ⚠️ DEPRECADO: Este formulario ya no se usa, el sistema utiliza
    el sistema de autenticación unificado en /auth/login/

    Se mantiene por compatibilidad pero redirige al login unificado.

    Fields:
        - usuario: Nombre de usuario o email
        - contrasena: Contraseña del usuario
    """
    usuario = forms.CharField(widget=forms.TextInput(attrs={'class':'sign'}))
    contrasena = forms.CharField(widget=forms.PasswordInput(attrs={'class':'sign'}))


class DesUrUsersConfig(forms.ModelForm):
    """
    Formulario LEGACY para configuración de usuarios de DesUr

    ⚠️ DEPRECADO: Usar en su lugar portaldu.cmin.forms.UsersConfig

    Permite actualizar:
    - Nombre de usuario
    - Foto de perfil
    - Contraseña (opcional)

    Fields:
        - username: Nombre de usuario (opcional para actualización)
        - foto: Fotografía de perfil (opcional)
        - password: Nueva contraseña (opcional)
        - confirmP: Confirmación de nueva contraseña (opcional)

    Validations:
        - Si se proporciona contraseña, debe coincidir con confirmación
        - Si se proporciona confirmación, debe haber contraseña
        - Todos los campos son opcionales (actualización parcial)
    """
    # Campos de contraseña opcionales para actualización
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)
    confirmP = forms.CharField(widget=forms.PasswordInput(attrs={'class':'formcontrol'}), required=False)

    class Meta:
        model = Users  # Usar el modelo Users unificado de CMIN
        fields = ['username', 'foto']
        widgets = {
            'username': forms.TextInput(attrs={'class':'formcontrol'}),
            'foto': forms.FileInput(attrs={'class':'foto', 'accept':'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicialización del formulario marcando todos los campos como opcionales
        Permite actualización parcial de datos
        """
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['foto'].required = False

    def clean(self):
        """
        Validación de contraseñas para actualización

        Returns:
            dict: Datos limpiados y validados

        Validations:
            - Si hay password, debe haber confirmP y deben coincidir
            - Si hay confirmP, debe haber password
        """
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
        """
        Guarda actualización de usuario con contraseña encriptada si se proporciona

        Args:
            commit (bool): Si True, guarda inmediatamente en BD

        Returns:
            Users: Instancia del usuario actualizado
        """
        user = super().save(commit=False)

        # Solo actualizar contraseña si se proporcionó una nueva
        if self.cleaned_data.get("password"):
          user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user


class GeneralRender(forms.ModelForm):
    """
    Formulario para datos generales de propuestas de Presupuesto Participativo

    Este formulario captura la información básica de cualquier proyecto de PP
    antes de pasar al formulario específico según la categoría seleccionada.

    Funcionalidades:
    - Captura de datos del promovente
    - Ubicación y descripción del proyecto
    - Evaluación del estado de instalaciones básicas (CFE, agua, drenaje, etc.)
    - Validación de teléfono con formato de 10 dígitos
    - Almacenamiento dinámico en JSONField de estados de instalaciones

    Fields:
        - nombre_promovente: Nombre del ciudadano que propone el proyecto
        - telefono: Teléfono de contacto (10 dígitos, inicia con 6)
        - categoria: Tipo de proyecto (parque, escuela, cs, infraestructura, pluviales)
        - direccion_proyecto: Ubicación del proyecto propuesto
        - desc_p: Descripción detallada del proyecto
        - notas_importantes: Notas adicionales relevantes
        - cfe: Estado de instalación eléctrica (bueno/regular/malo)
        - agua: Estado de instalación de agua potable
        - drenaje: Estado de instalación de drenaje
        - impermeabilizacion: Estado de impermeabilización
        - climas: Estado de aires acondicionados/calefacción
        - alumbrado: Estado de alumbrado público

    Flow:
        1. Usuario llena datos generales y selecciona categoría
        2. Sistema guarda datos en PpGeneral
        3. Redirige a formulario específico según categoría
        4. Formulario específico se vincula con PpGeneral via FK

    Storage:
        Los estados de instalaciones se guardan como JSONField:
        {'cfe': 'bueno', 'agua': 'regular', 'drenaje': 'malo', ...}
    """

    # Campos personalizados para estado de instalaciones (RadioSelect)
    # Se guardan en JSONField 'instalation_choices' del modelo
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

    # Campo personalizado para teléfono con validación estricta
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
        """
        Valida el formato del teléfono para Chihuahua

        Returns:
            str: Teléfono limpio de 10 dígitos

        Raises:
            ValidationError: Si el formato es inválido

        Validations:
            - Exactamente 10 dígitos
            - Debe iniciar con 6 (código de Chihuahua)
            - Remueve espacios, guiones y paréntesis automáticamente
        """
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
        # Excluir campos autogenerados y de sistema
        exclude = ['pp_ID', 'fecha_pp', 'calle_p', 'colonia_p', 'cp_p', 'fuuid']

        widgets = {
            'nombre_promovente':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre del promovente'}),
            'categoria':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Categoría del proyecto'}),
            'direccion_proyecto':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Dirección del proyecto'}),
            'desc_p':forms.Textarea(attrs={'class':'form-control', 'placeholder':'Descripción del proyecto'}),
            'notas_importantes':forms.Textarea(attrs={'class':'form-control', 'placeholder':'Notas importantes'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicialización del formulario con carga de datos de instalaciones desde JSON

        Si el formulario está en modo edición (instance.pk existe),
        carga los valores de instalation_choices al inicializar los campos.
        """
        super().__init__(*args, **kwargs)
        # Cargar estados de instalaciones desde JSONField si existe la instancia
        if self.instance.pk and self.instance.instalation_choices:
            for instalacion, estado in self.instance.instalation_choices.items():
                if instalacion in self.fields:
                    self.fields[instalacion].initial = estado

    def save(self, commit=True):
        """
        Guarda el formulario convirtiendo campos de instalaciones a JSONField

        Args:
            commit (bool): Si True, guarda inmediatamente en BD

        Returns:
            PpGeneral: Instancia del proyecto guardado

        Process:
            1. Obtiene valores de cada campo de instalación
            2. Construye diccionario con valores no vacíos
            3. Guarda diccionario en JSONField 'instalation_choices'
            4. Guarda el modelo
        """
        instance = super().save(commit=False)
        # Construir diccionario de estados de instalaciones
        instalation_choices = {}
        instalaciones = ['cfe', 'agua', 'drenaje', 'impermeabilizacion', 'climas', 'alumbrado']
        for instalacion in instalaciones:
            estado = self.cleaned_data.get(instalacion)
            if estado:  # Solo incluir si se seleccionó un estado
                instalation_choices[instalacion] = estado
        # Guardar en JSONField
        instance.instalation_choices = instalation_choices
        if commit:
            instance.save()
        print(self.cleaned_data)  # Debug: ver datos procesados
        return instance


class ParqueRender(forms.ModelForm):
    """
    Formulario específico para propuestas de mejoramiento de PARQUES

    Captura necesidades específicas de proyectos en parques públicos
    organizadas en 5 categorías principales:

    1. CANCHAS DEPORTIVAS:
       - Fútbol rápido, soccer, 7x7
       - Béisbol, softbol
       - Usos múltiples
       - Otras canchas

    2. ALUMBRADO:
       - Rehabilitación de alumbrado existente
       - Instalación de nuevo alumbrado

    3. JUEGOS Y RECREACIÓN:
       - Dog park (área para mascotas)
       - Juegos infantiles
       - Ejercitadores (gimnasio al aire libre)
       - Otros juegos

    4. TECHUMBRES:
       - Domos deportivos
       - Kioskos/gazebos

    5. EQUIPAMIENTO:
       - Botes de basura
       - Bancas
       - Andadores peatonales
       - Rampas de accesibilidad

    Fields:
        Todos los campos son checkboxes booleanos excepto:
        - notas_parque: Textarea para observaciones adicionales

    Widget:
        Todos usan clase 'check-form-control' para estilo consistente

    Linked to:
        - PpGeneral (via fk_pp): Datos generales del proyecto

    Template:
        pp/parque.html
    """

    class Meta:
        model = PpParque
        # Excluir ID y FK (se asignan automáticamente)
        exclude = ['p_parque_ID', 'fk_pp']

        # Widgets personalizados para todos los campos checkbox
        widgets = {
            # CANCHAS
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

            # ALUMBRADO
            'alumbrado_rehabilitacion': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'alumbrado_nuevo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # JUEGOS
            'juegos_dog_park': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'juegos_infantiles': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'juegos_ejercitadores': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'juegos_otros': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # TECHUMBRES
            'techumbre_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'techumbre_kiosko': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),

            # EQUIPAMIENTO
            'equipamiento_botes': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'equipamiento_bancas': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'equipamiento_andadores': forms.CheckboxInput(
              attrs={'class': 'check-form-control'}),
            'equipamiento_rampas': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),

            # NOTAS
            'notas_parque':forms.Textarea(attrs={'class':'text-form-control'}),
        }

class EscuelaRender(forms.ModelForm):
    """
    Formulario específico para propuestas de mejoramiento de ESCUELAS

    Captura necesidades específicas de proyectos en escuelas públicas
    organizadas en 3 categorías principales:

    1. REHABILITACIÓN:
       - Baños escolares
       - Salones de clase
       - Sistema eléctrico
       - Gimnasio
       - Otras áreas

    2. CONSTRUCCIÓN NUEVA:
       - Domos deportivos
       - Aulas/salones

    3. ÁREAS DEPORTIVAS:
       - Cancha de fútbol rápido
       - Cancha de fútbol soccer
       - Cancha de fútbol 7x7

    Fields:
        - nom_escuela: Nombre oficial de la escuela (TextInput)
        - Campos booleanos para cada tipo de mejora
        - notas_escuela: Observaciones adicionales (Textarea)

    Linked to:
        - PpGeneral (via fk_pp): Datos generales del proyecto

    Template:
        pp/escuela.html
    """
    class Meta:
        model = PpEscuela
        exclude = ['p_escuela_ID', 'fk_pp']

        widgets = {
            # DATOS BÁSICOS
            'nom_escuela':forms.TextInput(attrs={'class':'form-control'}),

            # REHABILITACIÓN
            'rehabilitacion_baños':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'rehabilitacion_salones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_electricidad': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),
            'rehabilitacion_gimnasio': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_otro': forms.CheckboxInput(
               attrs={'class': 'check-form-control'}),

            # CONSTRUCCIÓN
            'contruccion_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_aula': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # CANCHAS
            'cancha_futbol_rapido': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'cancha_futbol_soccer': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'cancha_futbol_7x7': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # NOTAS
            'notas_escuela': forms.Textarea(attrs={'class': 'text-form-control'}),
        }

class CsRender(forms.ModelForm):
    """
    Formulario para propuestas de CENTROS COMUNITARIOS y SALONES DE USOS MÚLTIPLES

    Captura necesidades de espacios comunitarios organizadas en 2 categorías:

    1. REHABILITACIÓN:
       - Baños
       - Salones/espacios
       - Sistema eléctrico
       - Gimnasio/áreas deportivas

    2. CONSTRUCCIÓN NUEVA:
       - Domos
       - Salones de usos múltiples
       - Otras construcciones

    Fields:
        Todos los campos son checkboxes booleanos excepto:
        - notas_propuesta: Textarea para observaciones

    Use Cases:
        - Centros comunitarios vecinales
        - Salones de juntas
        - Espacios para eventos sociales
        - Áreas de reunión ciudadana

    Linked to:
        - PpGeneral (via fk_pp): Datos generales del proyecto

    Template:
        pp/centro_salon.html
    """
    class Meta:
        model = PpCS
        exclude = ['p_cs_ID', 'fk_pp']

        widgets = {
            # REHABILITACIÓN
            'rehabilitacion_baños': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_salones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_electricidad': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'rehabilitacion_gimnasio': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # CONSTRUCCIÓN
            'contruccion_domo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_salon': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'construccion_otro': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # NOTAS
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),
        }

class InfraestructuraRender(forms.ModelForm):
    """
    Formulario para propuestas de INFRAESTRUCTURA URBANA

    Captura necesidades de obra civil e infraestructura vial organizadas en 3 categorías:

    1. INFRAESTRUCTURA CIVIL:
       - Bardas perimetrales
       - Banquetas peatonales
       - Muros de contención
       - Camellones
       - Mejora de cruceros
       - Ordenamiento vial
       - Entronques y rampas
       - Mejoras viales
       - Infraestructura peatonal
       - Bayonetas
       - Topes/reductores de velocidad
       - Puentes vehiculares

    2. PAVIMENTACIÓN:
       - Asfalto nuevo
       - Concreto hidráulico
       - Rehabilitación de pavimento existente

    3. SEÑALAMIENTO:
       - Pintura vial (rayas, cebras, flechas)
       - Señales verticales (alto, ceda el paso, etc.)

    Fields:
        Todos los campos son checkboxes booleanos excepto:
        - notas_propuesta: Textarea para detalles adicionales

    Use Cases:
        - Mejoramiento de vialidades
        - Seguridad peatonal
        - Accesibilidad urbana
        - Ordenamiento de tráfico

    Linked to:
        - PpGeneral (via fk_pp): Datos generales del proyecto

    Template:
        pp/infraestructura.html
    """
    class Meta:
        model = PpInfraestructura
        exclude = ['pp_infraestructura_id', 'fk_pp']

        widgets = {
            # INFRAESTRUCTURA
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

            # PAVIMENTACIÓN
            'pavimentacion_asfalto': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pavimentacion_concreto': forms.CheckboxInput(
                attrs={"class": 'check-form-control'}),
            'paviemntacion_rehabilitacion': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # SEÑALAMIENTO
            'señalamiento_pintura': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'señalamiento_señales': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # NOTAS
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),

        }

class PluvialRender(forms.ModelForm):
    """
    Formulario para propuestas de SOLUCIONES PLUVIALES

    Captura necesidades de manejo de agua pluvial y prevención de inundaciones.
    Especialmente relevante en Chihuahua por las lluvias torrenciales de verano.

    Categorías de obras pluviales:

    1. CONTENCIÓN Y CANALIZACIÓN:
       - Muros de contención
       - Canalización de arroyos
       - Puentes peatonales sobre arroyos
       - Vados (cruces de agua)
       - Puentes vehiculares

    2. DESALOJO DE AGUA:
       - Sistemas de desalojo pluvial
       - Rejillas pluviales
       - Lavaderos/alcantarillas
       - Obras hidráulicas especiales

    3. PROTECCIÓN:
       - Reposición de pisos dañados por agua
       - Protección contra inundaciones

    Fields:
        Todos los campos son checkboxes booleanos excepto:
        - notas_propuesta: Textarea para detalles técnicos

    Use Cases:
        - Prevención de inundaciones en temporada de lluvias
        - Protección de viviendas en zonas de riesgo
        - Canalización de arroyos naturales
        - Mejora de drenaje pluvial urbano

    Linked to:
        - PpGeneral (via fk_pp): Datos generales del proyecto

    Template:
        pp/pluviales.html
    """
    class Meta:
        model = PpPluvial
        exclude = ['pp_pluvial_ID', 'fk_pp']

        widgets = {
            # CONTENCIÓN Y CANALIZACIÓN
            'pluvial_muro_contencion':forms.CheckboxInput(attrs={'class':'check-form-control'}),
            'pluvial_canaliazacion': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_puente_peatonal': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_vado': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_puente': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # DESALOJO
            'pluvial_desalojo': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_rejillas': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_lavaderos': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_obra_hidraulica': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # PROTECCIÓN
            'pluvial_reposicion_piso': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),
            'pluvial_proteccion_inundaciones': forms.CheckboxInput(
                attrs={'class': 'check-form-control'}),

            # NOTAS
            'notas_propuesta': forms.Textarea(attrs={'class': 'text-form-control'}),

        }
