"""
Formularios del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema de formularios para gestión de usuarios y administración

Este módulo contiene todos los formularios del sistema CIVITAS - CMIN,
incluyendo formularios de autenticación, gestión de usuarios, configuración
de perfiles y carga de archivos Excel.

Características principales:
- Formularios con validación de permisos por roles
- Widgets personalizados con estilos CSS
- Validaciones de seguridad y integridad de datos
- Formularios responsivos para diferentes dispositivos
"""

from django import forms
from django.forms import ModelForm
from .models import Users

class UsersRender(forms.ModelForm):
    """
    Formulario para creación de nuevos usuarios del sistema.

    Incluye validaciones de permisos basadas en el rol del usuario creador
    y controles de seguridad para evitar escalación de privilegios.

    Funcionalidades:
    - Validación de confirmación de contraseña
    - Control de roles asignables según permisos del creador
    - Validación de unicidad de email y username
    - Campos condicionales según nivel de permisos
    """

    # Campo de contraseña con widget seguro
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'formcontrol'}),
        help_text="Contraseña del nuevo usuario (mínimo 8 caracteres)"
    )

    # Campo de confirmación de contraseña
    confirmP = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'formcontrol'}),
        help_text="Confirmar contraseña (debe coincidir exactamente)"
    )

    class Meta:
        model = Users
        fields = [
            'email',        # Correo electrónico (campo de autenticación principal)
            'first_name',   # Nombre(s) del usuario
            'last_name',    # Apellidos del usuario
            'username',     # Nombre de usuario único
            'bday',         # Fecha de nacimiento
            'password',     # Contraseña (se procesa por separado)
            'foto',         # Fotografía de perfil
            'rol',          # Rol del usuario en el sistema
            'is_staff',     # Permisos de staff (solo para administradores)
            'is_superuser'  # Permisos de superusuario (solo para administradores)
        ]

        # Widgets personalizados con estilos CSS uniformes
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'formcontrol',
                'placeholder': 'usuario@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'formcontrol',
                'placeholder': 'Nombre(s)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'formcontrol',
                'placeholder': 'Apellidos'
            }),
            'username': forms.TextInput(attrs={
                'class': 'formcontrol',
                'placeholder': 'Nombre de usuario único'
            }),
            'bday': forms.DateInput(attrs={
                'class': 'formcontrol',
                'type': 'date'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'foto',
                'accept': 'image/*'  # Solo imágenes
            }),
            'rol': forms.Select(attrs={
                'class': 'formcontrol'
            }),
        }

    def __init__(self, *args, creator_user=None, **kwargs):
        """
        Inicializa el formulario con validaciones de permisos basadas en el usuario creador.

        Args:
            creator_user (Users): Usuario que está creando el nuevo usuario
            *args: Argumentos posicionales estándar de Django
            **kwargs: Argumentos de palabra clave estándar de Django
        """
        super().__init__(*args, **kwargs)
        self.creator_user = creator_user

        # Controlar qué roles puede crear según el rol del creador
        if self.creator_user is None or self.creator_user.rol != 'administrador':
            # Solo administradores pueden crear otros administradores
            self.fields['rol'].choices = [
                ('delegador', 'Delegador'),
                ('campo', 'Campo'),
            ]
            # Remover campos de permisos avanzados para no administradores
            self.fields.pop('is_staff', None)
            self.fields.pop('is_superuser', None)
            self.fields.pop('groups', None)
            self.fields.pop('user_permissions', None)

    def clean(self):
        """
        Validaciones personalizadas del formulario.

        Returns:
            dict: Datos limpiados y validados

        Raises:
            ValidationError: Si las validaciones fallan
        """
        cleaned_data = super().clean()

        # Validar coincidencia de contraseñas
        password = cleaned_data.get('password')
        confirmP = cleaned_data.get('confirmP')
        if password != confirmP:
            self.add_error('confirmP', "Las contraseñas no coinciden")

        # Validar permisos de rol
        if self.creator_user:
            rol = cleaned_data.get('rol')
            if rol == 'administrador' and self.creator_user.rol != 'administrador':
                self.add_error('rol', "Solo administradores pueden crear otros administradores")

            # Validar permisos de staff
            is_staff = cleaned_data.get('is_staff', False)
            if is_staff and not self.creator_user.can_create_user_type(True, False):
                self.add_error('is_staff', "No tienes permisos para crear usuarios staff")

            # Validar permisos de superusuario
            is_superuser = cleaned_data.get('is_superuser', False)
            if is_superuser and not self.creator_user.is_superuser:
                self.add_error('is_superuser', "Solo superusuarios pueden crear otros superusuarios")

        return cleaned_data

    def save(self, commit=True):
        """
        Guarda el usuario con la contraseña encriptada y validaciones adicionales.

        Args:
            commit (bool): Si guardar inmediatamente en la base de datos

        Returns:
            Users: Instancia del usuario creado
        """
        user = super().save(commit=False)

        # Encriptar contraseña antes de guardar
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        # Asignar permisos automáticos según rol
        if user.rol == 'administrador':
            user.is_staff = True
            user.is_superuser = True
        elif user.rol == 'delegador':
            user.is_staff = True
            user.is_superuser = False
        else:  # campo
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

        return user


class Login(forms.Form):
    """
    Formulario de autenticación del sistema.

    Formulario simple y seguro para el inicio de sesión de usuarios,
    compatible con el sistema unificado de autenticación CMIN/DesUr.

    Funcionalidades:
    - Campos de usuario y contraseña con validación básica
    - Widgets seguros para protección de contraseñas
    - Compatibilidad con migración automática de usuarios legacy
    """

    # Campo de usuario (puede ser username o email)
    usuario = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'formcontrol',
            'placeholder': 'Usuario',
            'required': True
        }),
        help_text="Ingrese su nombre de usuario o correo electrónico"
    )

    # Campo de contraseña con widget seguro
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'formcontrol',
            'placeholder': 'Contraseña',
            'required': True
        }),
        help_text="Ingrese su contraseña"
    )

    def clean(self):
        """
        Validaciones básicas del formulario de login.

        Returns:
            dict: Datos limpiados para autenticación
        """
        cleaned_data = super().clean()
        usuario = cleaned_data.get('usuario')
        contrasena = cleaned_data.get('contrasena')

        # Validar que ambos campos estén presentes
        if not usuario or not contrasena:
            raise forms.ValidationError("Usuario y contraseña son requeridos")

        return cleaned_data


class UsersConfig(forms.ModelForm):
    """
    Formulario para configuración del perfil personal del usuario.

    Permite a los usuarios actualizar su información personal, cambiar
    su fotografía de perfil y modificar datos de contacto.

    Funcionalidades:
    - Actualización de datos personales
    - Cambio de fotografía de perfil
    - Validación de campos opcionales
    - Preservación de campos sensibles (roles, permisos)
    """

    class Meta:
        model = Users
        fields = [
            'first_name',   # Nombre(s) modificable
            'last_name',    # Apellidos modificables
            'email',        # Email (con validaciones especiales)
            'foto',         # Fotografía de perfil
        ]

        # Widgets con estilos personalizados
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre(s)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'  # Solo archivos de imagen
            }),

        }

    def clean_email(self):
        """
        Validación especial para el campo email.

        Verifica que el email no esté en uso por otro usuario,
        excepto por el usuario actual que está editando su perfil.

        Returns:
            str: Email validado

        Raises:
            ValidationError: Si el email ya está en uso
        """
        email = self.cleaned_data.get('email')

        # Verificar unicidad del email (excepto para el usuario actual)
        if email and self.instance:
            existing_user = Users.objects.filter(email=email).exclude(pk=self.instance.pk).first()
            if existing_user:
                raise forms.ValidationError("Este email ya está en uso por otro usuario")

        return email

    def clean_telefono(self):
        """
        Validación del número de teléfono.

        Returns:
            str: Teléfono validado y formateado
        """
        telefono = self.cleaned_data.get('telefono')

        # Permitir campo vacío
        if not telefono:
            return telefono

        # Limpiar formato del teléfono (solo números, espacios, guiones, paréntesis)
        import re
        if not re.match(r'^[\d\s\-\(\)\+]+$', telefono):
            raise forms.ValidationError("Formato de teléfono inválido")

        return telefono


class UploadExcel(forms.Form):
    """
    Formulario para carga de archivos Excel con datos de licitaciones.

    Permite la importación masiva de licitaciones desde archivos Excel
    con validación de formato y estructura de datos.

    Funcionalidades:
    - Validación de tipo de archivo (solo Excel)
    - Verificación de tamaño máximo
    - Validación de estructura de columnas requeridas
    - Procesamiento con pandas para análisis de datos
    """

    # Campo de archivo con validaciones específicas
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',  # Solo archivos Excel
            'required': True
        }),
        help_text="Seleccione un archivo Excel (.xlsx o .xls) con las columnas: 'Fecha límite', 'No. licitación', 'Descripción'"
    )

    def clean_file(self):
        """
        Validación del archivo Excel subido.

        Returns:
            File: Archivo validado listo para procesamiento

        Raises:
            ValidationError: Si el archivo no cumple los requisitos
        """
        file = self.cleaned_data.get('file')

        if file:
            # Validar tamaño máximo (10MB)
            max_size = 10 * 1024 * 1024  # 10MB en bytes
            if file.size > max_size:
                raise forms.ValidationError("El archivo es demasiado grande. Máximo 10MB.")

            # Validar extensión del archivo
            allowed_extensions = ['.xlsx', '.xls']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError("Solo se permiten archivos Excel (.xlsx, .xls)")

            # Validar que el archivo no esté vacío
            if file.size == 0:
                raise forms.ValidationError("El archivo está vacío")

        return file

    def clean(self):
        """
        Validaciones adicionales del formulario.

        Returns:
            dict: Datos validados del formulario
        """
        cleaned_data = super().clean()
        file = cleaned_data.get('file')

        if file:
            try:
                # Intentar leer el archivo con pandas para validar estructura
                import pandas as pd
                df = pd.read_excel(file, nrows=1)  # Solo leer primera fila para validar

                # Columnas requeridas en el Excel
                required_columns = ['Fecha límite', 'No. licitación', 'Descripción']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    raise forms.ValidationError(
                        f"Faltan las siguientes columnas en el archivo: {', '.join(missing_columns)}"
                    )

                # Resetear el puntero del archivo para uso posterior
                file.seek(0)

            except Exception as e:
                if "missing_columns" not in str(e):
                    raise forms.ValidationError(f"Error al procesar el archivo Excel: {str(e)}")

        return cleaned_data


class CambioPasswordForm(forms.Form):
    """
    Formulario para cambio de contraseña del usuario.

    Permite a los usuarios cambiar su contraseña actual por una nueva,
    con validaciones de seguridad y confirmación.

    Funcionalidades:
    - Verificación de contraseña actual
    - Validación de fortaleza de nueva contraseña
    - Confirmación de nueva contraseña
    - Encriptación automática
    """

    # Contraseña actual para verificación
    password_actual = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        }),
        help_text="Ingrese su contraseña actual para verificar identidad"
    )

    # Nueva contraseña
    password_nueva = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        help_text="Mínimo 8 caracteres, debe incluir letras y números"
    )

    # Confirmación de nueva contraseña
    password_confirmacion = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        help_text="Repita la nueva contraseña"
    )

    def __init__(self, user=None, *args, **kwargs):
        """
        Inicializar formulario con usuario actual.

        Args:
            user (Users): Usuario que está cambiando la contraseña
        """
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password_actual(self):
        """
        Validar que la contraseña actual sea correcta.

        Returns:
            str: Contraseña actual validada

        Raises:
            ValidationError: Si la contraseña actual es incorrecta
        """
        password_actual = self.cleaned_data.get('password_actual')

        if self.user and not self.user.check_password(password_actual):
            raise forms.ValidationError("La contraseña actual es incorrecta")

        return password_actual

    def clean_password_nueva(self):
        """
        Validar fortaleza de la nueva contraseña.

        Returns:
            str: Nueva contraseña validada

        Raises:
            ValidationError: Si la contraseña no cumple los requisitos
        """
        password_nueva = self.cleaned_data.get('password_nueva')

        # Validar longitud mínima
        if len(password_nueva) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres")

        # Validar que contenga letras y números
        import re
        if not re.search(r'[A-Za-z]', password_nueva):
            raise forms.ValidationError("La contraseña debe contener al menos una letra")

        if not re.search(r'\d', password_nueva):
            raise forms.ValidationError("La contraseña debe contener al menos un número")

        return password_nueva

    def clean(self):
        """
        Validar que las contraseñas nuevas coincidan.

        Returns:
            dict: Datos validados del formulario
        """
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get('password_nueva')
        password_confirmacion = cleaned_data.get('password_confirmacion')

        if password_nueva and password_confirmacion:
            if password_nueva != password_confirmacion:
                self.add_error('password_confirmacion', "Las contraseñas no coinciden")

        return cleaned_data
