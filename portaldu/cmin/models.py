"""
Modelos de datos para el sistema CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema unificado de usuarios y gestión administrativa
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import AutoField


class CustomUser(BaseUserManager):
    """
    Manager personalizado para el modelo Users
    Proporciona métodos específicos para crear usuarios con validación de permisos
    """

    def create_user(self, email, password=None, creator_user=None, is_staff=False, is_superuser=False, **extra_fields):
        """
        Crea un usuario regular con validación de permisos del creador

        Args:
            email (str): Correo electrónico único del usuario
            password (str): Contraseña sin encriptar
            creator_user (Users): Usuario que está creando este nuevo usuario
            is_staff (bool): Si el usuario tendrá permisos de staff
            is_superuser (bool): Si el usuario tendrá permisos de superusuario
            **extra_fields: Campos adicionales del modelo Users
        """
        target_is_staff = extra_fields.pop('is_staff', is_staff)
        target_is_superuser = extra_fields.pop('is_superuser', is_superuser)

        # Validar que el usuario creador tenga permisos para crear el tipo de usuario solicitado
        if creator_user is not None:
            if not creator_user.can_create_user_type(is_staff, is_superuser):
                user_type = 'superusuario' if is_superuser else 'staff' if is_staff else 'invitado'
                raise PermissionError(f"No tienes permiso para crear un usuario de tipo {user_type}")

        # Validar que se proporcione email (campo requerido)
        if not email:
            raise ValueError("Ingrese email")

        # Normalizar email y crear usuario
        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=target_is_staff, is_superuser=target_is_superuser, **extra_fields)
        user.set_password(password)  # Encriptar contraseña automáticamente
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea un superusuario con permisos administrativos completos

        Args:
            email (str): Correo electrónico único del superusuario
            password (str): Contraseña sin encriptar
            **extra_fields: Campos adicionales del modelo Users
        """
        # Configurar valores por defecto para superusuario
        extra_fields.setdefault('is_staff', True)        # Acceso al admin de Django
        extra_fields.setdefault('is_superuser', True)    # Permisos completos
        extra_fields.setdefault('is_active', True)       # Usuario activo
        extra_fields.setdefault('rol', 'administrador')  # Rol administrativo

        # Validar configuración de superusuario
        if not extra_fields.get('is_staff'):
            raise ValueError('El superusuario debe tener is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, password, **extra_fields)

    def get_superusers(self):
        """Obtiene todos los superusuarios del sistema"""
        return self.filter(is_superuser=True)

    def get_staff(self):
        """Obtiene usuarios con permisos de staff (pero no superusuarios)"""
        return self.filter(is_staff=True, is_superuser=False)

    def get_regular(self):
        """Obtiene usuarios regulares sin permisos especiales"""
        return self.filter(is_staff=False, is_superuser=False)


class Users(AbstractUser, PermissionsMixin):
    """
    Modelo unificado de usuarios del sistema
    Extiende AbstractUser de Django para incluir roles específicos y campos adicionales
    """

    # Opciones de roles disponibles en el sistema
    ROLE_CHOICES = [
        ('administrador', 'Administrador'),  # Acceso completo CMIN + DesUr + gestión usuarios
        ('delegador', 'Delegador'),         # Acceso CMIN + visualización datos + reportes
        ('campo', 'Campo'),                 # Acceso solo DesUr para trabajo de campo
    ]
    
    # === CAMPOS ADICIONALES AL MODELO ESTÁNDAR DE DJANGO ===

    # Email único - requerido para autenticación
    email = models.EmailField(unique=True)

    # Fecha de nacimiento del usuario - opcional
    bday = models.DateField(null=True, blank=True)

    # Foto de perfil del usuario - almacenada en carpeta 'fotos/'
    foto = models.ImageField(upload_to='fotos', null=True, blank=True)

    # Rol del usuario - determina permisos y accesos del sistema
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='campo')

    # === CONFIGURACIÓN DE AUTENTICACIÓN ===

    # Campo usado para login (username en lugar de email)
    USERNAME_FIELD = 'username'

    # Campos requeridos además del USERNAME_FIELD y password
    REQUIRED_FIELDS = ['first_name', 'email']

    # Manager personalizado para manejo de usuarios
    objects = CustomUser()

    class Meta:
        db_table = 'cmin_users'    # Tabla: cmin_users
        ordering = ['username']    # Ordenar por nombre de usuario

    def __str__(self):
        return self.username

    @property
    def get_user_type(self):
        """
        Obtiene el tipo de usuario basado en permisos Django

        Returns:
            str: Tipo de usuario ('Superman', 'Staff', 'Regular')
        """
        if self.is_superuser:
            return 'Superman'
        elif self.is_staff:
            return 'Staff'
        else:
            return 'Regular'

    @property
    def get_role_display_name(self):
        """
        Obtiene el nombre legible del rol del usuario

        Returns:
            str: Nombre del rol o 'Sin rol' si no está definido
        """
        return dict(self.ROLE_CHOICES).get(self.rol, 'Sin rol')

    def can_create_user_type(self, target_is_staff, target_is_superuser):
        """
        Valida si el usuario actual puede crear un usuario del tipo especificado

        Args:
            target_is_staff (bool): Si el usuario objetivo será staff
            target_is_superuser (bool): Si el usuario objetivo será superusuario

        Returns:
            bool: True si puede crear el tipo de usuario, False si no
        """
        if self.is_superuser:
            return True  # Superusuarios pueden crear cualquier tipo
        elif self.is_staff:
            # Staff solo puede crear usuarios regulares
            return not target_is_staff and not target_is_superuser
        else:
            return False  # Usuarios regulares no pueden crear otros usuarios

    def get_allowed_user(self):
        """
        Obtiene los tipos de usuario que este usuario puede crear

        Returns:
            list: Lista de tuplas (código, nombre) de tipos permitidos
        """
        if self.is_superuser:
            return [
                ('superuser', 'Superusuario'),
                ('staff', 'Staff'),
                ('user', 'Invitado'),
            ]
        elif self.is_staff:
            return [('user', 'Invitado')]
        else:
            return []

    def can_manage_users(self):
        """
        Verifica si el usuario puede gestionar otros usuarios

        Returns:
            bool: True si puede gestionar usuarios
        """
        return self.is_superuser or self.is_staff

    def get_manageable_user(self):
        """
        Obtiene el queryset de usuarios que este usuario puede gestionar

        Returns:
            QuerySet: Usuarios gestionables por este usuario
        """
        if self.is_superuser:
            return Users.objects.all()
        elif self.is_staff:
            # Staff solo puede gestionar usuarios regulares
            return Users.objects.filter(is_staff=False, is_superuser=False)
        else:
            return Users.objects.none()

    # === MÉTODOS DE PERMISOS POR ROL ===

    def has_cmin_access(self):
        """
        Verifica si el usuario tiene acceso al módulo CMIN

        Returns:
            bool: True si tiene acceso (administrador o delegador)
        """
        return self.rol in ['administrador', 'delegador']

    def has_desur_access(self):
        """
        Verifica si el usuario tiene acceso al módulo DesUr

        Returns:
            bool: True si tiene acceso (campo o administrador)
        """
        return self.rol in ['campo', 'administrador']

    def can_access_tables(self):
        """
        Verifica si el usuario puede acceder a tablas y reportes

        Returns:
            bool: True si puede acceder (administrador o delegador)
        """
        return self.rol in ['administrador', 'delegador']

    def can_access_seguimiento(self):
        """
        Verifica si el usuario puede hacer seguimiento de trámites

        Returns:
            bool: True si puede hacer seguimiento (administrador o delegador)
        """
        return self.rol in ['administrador', 'delegador']

    def can_access_admin(self):
        """
        Verifica si el usuario puede acceder a funciones administrativas

        Returns:
            bool: True si puede acceder (solo administrador)
        """
        return self.rol == 'administrador'

    def can_create_users(self):
        """
        Verifica si el usuario puede crear otros usuarios

        Returns:
            bool: True si puede crear usuarios (solo administrador)
        """
        return self.rol == 'administrador'

    def can_manage_licitaciones(self):
        """
        Verifica si el usuario puede gestionar licitaciones

        Returns:
            bool: True si puede gestionar (solo administrador)
        """
        return self.rol == 'administrador'

    # === MÉTODOS PARA COMPATIBILIDAD CON DESUR ===

    def get_full_name(self):
        """
        Obtiene el nombre completo del usuario
        Método para compatibilidad con DesUrUsers legacy

        Returns:
            str: Nombre completo del usuario
        """
        return super().get_full_name()

    def get_short_name(self):
        """
        Obtiene el nombre corto del usuario
        Método para compatibilidad con DesUrUsers legacy

        Returns:
            str: Primer nombre del usuario
        """
        return self.first_name


class LoginDate(models.Model):
    """
    Modelo unificado para registro de fechas de login
    Reemplaza tanto los login de CMIN como DesUr en un solo modelo
    """

    # Clave primaria autoincremental del registro de login
    login_ID = models.AutoField(primary_key=True)

    # Usuario que realizó el login - referencia al modelo unificado Users
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Usuario')

    # Fecha y hora del login - se asigna automáticamente
    date = models.DateTimeField(auto_now_add=True)

    # Módulo desde el cual se realizó el login (CMIN/DesUr) - opcional
    module = models.CharField(max_length=20, null=True, blank=True,
                             choices=[('CMIN', 'CMIN'), ('DesUr', 'DesUr')])

    class Meta:
        db_table = 'LoginDate'     # Tabla: LoginDate
        ordering = ['-date']       # Ordenar por fecha descendente (más recientes primero)
        verbose_name = "Fecha de Login"

    def __str__(self):
        return f"{self.user_FK.username} - {self.date.strftime('%d/%m/%Y %H:%M')}"

    @classmethod
    def create(cls, user, module=None):
        """
        Crea un nuevo registro de login para el usuario especificado

        Args:
            user (Users): Usuario que realizó el login
            module (str): Módulo desde el cual se realizó el login ('CMIN' o 'DesUr')

        Returns:
            LoginDate: Instancia del registro creado
        """
        return cls.objects.create(user_FK=user, module=module)

class SolicitudesPendientes(models.Model):
    """
    Modelo para almacenar solicitudes que están pendientes de procesamiento.

    Representa el estado intermedio entre la recepción de una solicitud
    desde DesUr y su procesamiento/envío por parte de los administradores.
    """

    # Clave primaria autoincremental de la solicitud pendiente
    solicitud_ID = models.AutoField(primary_key=True)

    # Nombre descriptivo de la solicitud - máximo 150 caracteres
    nomSolicitud = models.CharField(max_length=150)

    # Fecha en que se creó la solicitud
    fechaSolicitud = models.DateField()

    # Documento asociado desde el módulo DesUr - referencia foránea
    doc_FK = models.ForeignKey('desUr.Files', on_delete=models.CASCADE, verbose_name='documentos')

    # Email del destinatario al que se enviará la solicitud - opcional
    destinatario = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'SolicitudesPendientes'  # Tabla: SolicitudesPendientes
        ordering = ['solicitud_ID']         # Ordenar por ID ascendente

    def __str__(self):
        return self.nomSolicitud


class SolicitudesEnviadas(models.Model):
    """
    Modelo para registrar solicitudes que han sido procesadas y enviadas.

    Representa el estado activo de las solicitudes, con toda la información
    de seguimiento, asignación de responsables y control de estados.
    """

    # Opciones de prioridad para clasificación de solicitudes
    PRIORIDAD_CHOICES = [
        ('Baja', 'Baja'),      # Prioridad baja - no urgente
        ('Media', 'Media'),    # Prioridad media - normal
        ('Alta', 'Alta'),      # Prioridad alta - urgente
    ]

    # Clave primaria autoincremental de la solicitud enviada
    solicitud_ID = AutoField(primary_key=True)

    # Nombre descriptivo de la solicitud - máximo 150 caracteres
    nomSolicitud = models.CharField(max_length=150)

    # Fecha de envío - se actualiza automáticamente en cada modificación
    fechaEnvio = models.DateField(auto_now=True)

    # Usuario que procesó y envió la solicitud - referencia al modelo Users
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')

    # Documento asociado desde el módulo DesUr - referencia foránea
    doc_FK = models.ForeignKey('desUr.Files', on_delete=models.CASCADE, verbose_name='documentos')

    # Solicitud pendiente que dio origen a esta solicitud enviada
    solicitud_FK = models.ForeignKey(SolicitudesPendientes, on_delete=models.CASCADE, verbose_name='solicitudes')

    # Número de folio oficial de la solicitud - opcional, máximo 50 caracteres
    folio = models.CharField(max_length=50, null=True, blank=True)

    # Categoría o tipo de solicitud - opcional, máximo 100 caracteres
    categoria = models.CharField(max_length=100, null=True, blank=True)

    # Nivel de prioridad asignado a la solicitud - valor por defecto 'Media'
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='Media')

    # Usuario responsable de atender la solicitud - opcional con relación inversa
    usuario_asignado = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitudes_asignadas', verbose_name='Usuario Asignado'
    )

    # Estado actual de la solicitud en el proceso de atención
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),      # Esperando ser atendida
            ('en_proceso', 'En Proceso'),    # Siendo procesada
            ('completado', 'Completado')     # Finalizada
        ],
        default='pendiente'  # Estado inicial por defecto
    )

    class Meta:
        db_table = 'SolicitudesEnviadas'  # Tabla: SolicitudesEnviadas
        ordering = ['solicitud_ID']       # Ordenar por ID ascendente

    def __str__(self):
        return self.nomSolicitud

class Seguimiento(models.Model):
    """
    Modelo para documentar el seguimiento y progreso de solicitudes.

    Permite registrar actualizaciones, comentarios y documentos de evidencia
    durante el proceso de atención de las solicitudes.
    """

    # Clave primaria autoincremental del registro de seguimiento
    seguimiento_ID = models.AutoField(primary_key=True)

    # Solicitud a la que pertenece este seguimiento - referencia foránea
    solicitud_FK = models.ForeignKey(SolicitudesEnviadas, on_delete=models.CASCADE, verbose_name='solicitudes')

    # Usuario que registra este seguimiento - referencia al modelo Users
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')

    # Fecha de creación del seguimiento - se asigna automáticamente
    fechaSeguimiento = models.DateField(auto_now_add=True)

    # Comentarios u observaciones del seguimiento - texto largo
    comentario = models.TextField()

    # Documento de evidencia del seguimiento - archivo subido a 'seguimiento_docs/'
    documento = models.FileField(upload_to='seguimiento_docs/')

    # Nombre descriptivo del documento de seguimiento - máximo 200 caracteres
    nomSeg = models.CharField(max_length=200)

    class Meta:
        db_table = 'Seguimiento'      # Tabla: Seguimiento
        ordering = ['seguimiento_ID'] # Ordenar por ID ascendente

    def __str__(self):
        return f"Seguimiento {self.seguimiento_ID} - {self.solicitud_FK.nomSolicitud}"

class Close(models.Model):
    """
    Modelo para registrar el cierre formal de solicitudes.

    Representa la finalización oficial del proceso de atención de una solicitud,
    con comentarios finales y referencia al último seguimiento realizado.
    """

    # Clave primaria autoincremental del registro de cierre
    close_ID = models.AutoField(primary_key=True)

    # Solicitud que se está cerrando - referencia foránea
    solicitud_FK = models.ForeignKey(SolicitudesEnviadas, on_delete=models.CASCADE, verbose_name='solicitudes')

    # Usuario que realiza el cierre de la solicitud - referencia al modelo Users
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuarios')

    # Último seguimiento asociado al cierre - referencia foránea
    seguimiento_FK = models.ForeignKey(Seguimiento, on_delete=models.CASCADE, verbose_name='seguimiento')

    # Fecha de cierre - se asigna automáticamente al crear el registro
    fechaCierre = models.DateField(auto_now_add=True)

    # Comentarios finales sobre el cierre de la solicitud - texto largo
    comentario = models.TextField()

    class Meta:
        db_table = 'Close'    # Tabla: Close
        ordering = ['close_ID'] # Ordenar por ID ascendente

    def __str__(self):
        return f"Cierre {self.close_ID} - {self.solicitud_FK.nomSolicitud}"


class Notifications(models.Model):
    """
    Modelo de notificaciones del sistema
    Almacena mensajes y alertas para usuarios específicos
    """

    # Clave primaria autoincremental de la notificación
    notification_ID = models.AutoField(primary_key=True)

    # Usuario destinatario de la notificación - referencia al modelo unificado Users
    user_FK = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Mensaje de la notificación - texto completo
    msg = models.TextField()

    # URL opcional a la que apunta la notificación
    link = models.URLField(blank=True, null=True)

    # Estado de la notificación - si ha sido leída por el usuario
    is_read = models.BooleanField(default=False)

    # Fecha y hora de creación de la notificación - se asigna automáticamente
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'Notificaciones'           # Tabla: Notificaciones
        ordering = ['-created_at']            # Ordenar por fecha descendente (más recientes primero)

    def __str__(self):
        return self.msg or "Notificación sin mensaje"

    def mark_as_read(self):
        """
        Marca la notificación como leída
        """
        self.is_read = True
        self.save()

    def mark_as_unread(self):
        """
        Marca la notificación como no leída
        """
        self.is_read = False
        self.save()

    @classmethod
    def create_for_user(cls, user, message, link=None):
        """
        Crea una nueva notificación para un usuario específico

        Args:
            user (Users): Usuario destinatario
            message (str): Mensaje de la notificación
            link (str): URL opcional

        Returns:
            Notifications: Instancia de la notificación creada
        """
        return cls.objects.create(user_FK=user, msg=message, link=link)

    @classmethod
    def get_unread_for_user(cls, user):
        """
        Obtiene todas las notificaciones no leídas de un usuario

        Args:
            user (Users): Usuario del cual obtener notificaciones

        Returns:
            QuerySet: Notificaciones no leídas del usuario
        """
        return cls.objects.filter(user_FK=user, is_read=False)


class Licitaciones(models.Model):
    """
    Modelo de licitaciones de obra pública
    Almacena información sobre licitaciones activas y sus fechas límite
    """

    # Clave primaria autoincremental de la licitación
    licitacion_ID = models.AutoField(primary_key=True)

    # Fecha límite para participar en la licitación
    fecha_limite = models.DateField(blank=True, null=True)

    # Número oficial de la licitación - máximo 15 caracteres
    no_licitacion = models.CharField(max_length=15, blank=True, null=True)

    # Descripción detallada de la licitación - máximo 255 caracteres
    desc_licitacion = models.CharField(max_length=255, blank=True, null=True)

    # Estado de la licitación - si está activa para recibir participantes
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'Licitaciones'    # Tabla: Licitaciones
        ordering = ['-fecha_limite'] # Ordenar por fecha límite descendente

    def __str__(self):
        return f"{self.no_licitacion} - {self.desc_licitacion}"

    def is_expired(self):
        """
        Verifica si la licitación ha expirado

        Returns:
            bool: True si la fecha límite ya pasó
        """
        from django.utils import timezone
        if self.fecha_limite:
            return self.fecha_limite < timezone.now().date()
        return False

    def deactivate_if_expired(self):
        """
        Desactiva la licitación si ha expirado
        """
        if self.is_expired():
            self.activa = False
            self.save()

    @classmethod
    def get_active(cls):
        """
        Obtiene todas las licitaciones activas y no expiradas

        Returns:
            QuerySet: Licitaciones activas
        """
        from django.utils import timezone
        return cls.objects.filter(
            activa=True,
            fecha_limite__gte=timezone.now().date()
        )

    @classmethod
    def cleanup_expired(cls):
        """
        Desactiva automáticamente licitaciones expiradas

        Returns:
            int: Número de licitaciones desactivadas
        """
        from django.utils import timezone
        expired_count = cls.objects.filter(
            activa=True,
            fecha_limite__lt=timezone.now().date()
        ).update(activa=False)
        return expired_count


# === MODELOS PARA ENCUESTAS MÓVILES ===

class EncuestasOffline(models.Model):
    """
    Modelo para almacenar encuestas recibidas desde la aplicación móvil offline.

    Permite la sincronización de datos recopilados en dispositivos móviles
    cuando no hay conexión a internet disponible.
    """

    # Clave primaria autoincremental de la encuesta offline
    encuesta_ID = models.AutoField(primary_key=True)

    # UUID único generado por la aplicación móvil - máximo 100 caracteres
    f_uuid = models.CharField(blank=True, null=True, max_length=100)

    # Fecha de respuesta en formato string - máximo 100 caracteres
    fecha_respuesta = models.CharField(max_length=100, blank=True, null=True)

    # === DATOS DEMOGRÁFICOS DEL ENCUESTADO ===

    # Escuela donde se realizó la encuesta - máximo 255 caracteres
    escuela = models.CharField(max_length=255, blank=True, null=True)

    # Colonia o ubicación geográfica - máximo 255 caracteres
    colonia = models.CharField(max_length=255, blank=True, null=True)

    # Rol social del encuestado (estudiante, padre, maestro, etc.) - máximo 255 caracteres
    rol_social = models.CharField(max_length=255, blank=True, null=True)

    # Género del encuestado - máximo 100 caracteres
    genero = models.CharField(max_length=100, blank=True, null=True)

    # Nivel educativo del encuestado - máximo 100 caracteres
    nivel_escolar = models.CharField(max_length=100, blank=True, null=True)

    # Grado escolar específico - máximo 100 caracteres
    grado_escolar = models.CharField(max_length=100, blank=True, null=True)

    # Pertenencia a comunidad indígena - máximo 100 caracteres
    comunidad_indigena = models.CharField(max_length=100, blank=True, null=True)

    # Especificación de otra comunidad indígena - máximo 100 caracteres
    otro_comunidad_indigena = models.CharField(max_length=100, blank=True, null=True)

    # Pertenencia a grupo vulnerable - máximo 100 caracteres
    grupo_vulnerable = models.CharField(max_length=100, blank=True, null=True)

    # Especificación de otro grupo vulnerable - máximo 100 caracteres
    otro_grupo_vulnerable = models.CharField(max_length=100, blank=True, null=True)

    # Tipo de proyecto evaluado - máximo 100 caracteres
    tipo_proyecto = models.CharField(max_length=100, blank=True, null=True)

    # === PREGUNTAS DE LA ENCUESTA ===

    # Pregunta 1: Respuesta numérica (escala, calificación, etc.)
    pregunta_1 = models.IntegerField(blank=True, null=True)

    # Pregunta 2: Respuesta de opción múltiple - máximo 255 caracteres
    pregunta_2 = models.CharField(max_length=255, blank=True, null=True)

    # Especificación de "Otro" para pregunta 2 - máximo 255 caracteres
    otro_pregunta_2 = models.CharField(max_length=255, blank=True, null=True)

    # Pregunta 3: Respuesta abierta - máximo 255 caracteres
    pregunta_3 = models.CharField(max_length=255, blank=True, null=True)

    # Pregunta 4: Respuesta numérica
    pregunta_4 = models.IntegerField(blank=True, null=True)

    # Pregunta 5: Respuesta de opción múltiple - máximo 255 caracteres
    pregunta_5 = models.CharField(max_length=255, blank=True, null=True)

    # Preguntas 6-11: Respuestas numéricas (escalas de satisfacción, calificaciones)
    pregunta_6 = models.IntegerField(blank=True, null=True)
    pregunta_7 = models.IntegerField(blank=True, null=True)
    pregunta_8 = models.IntegerField(blank=True, null=True)
    pregunta_9 = models.IntegerField(blank=True, null=True)
    pregunta_10 = models.IntegerField(blank=True, null=True)
    pregunta_11 = models.IntegerField(blank=True, null=True)

    # Pregunta 12: Respuesta de opción múltiple - máximo 255 caracteres
    pregunta_12 = models.CharField(max_length=255, blank=True, null=True)

    # Especificación de "Otro" para pregunta 12 - máximo 255 caracteres
    otro_pregunta_12 = models.CharField(max_length=255, blank=True, null=True)

    # Preguntas 13-14: Respuestas numéricas
    pregunta_13 = models.IntegerField(blank=True, null=True)
    pregunta_14 = models.IntegerField(blank=True, null=True)

    # Pregunta 15: Respuesta de opción múltiple - máximo 255 caracteres
    pregunta_15 = models.CharField(max_length=255, blank=True, null=True)

    # Especificación de "Otro" para pregunta 15 - máximo 255 caracteres
    otro_pregunta_15 = models.CharField(max_length=255, blank=True, null=True)

    # Pregunta 16: Respuesta de opción múltiple - máximo 255 caracteres
    pregunta_16 = models.CharField(max_length=255, blank=True, null=True)

    # Especificación de "Otro" para pregunta 16 - máximo 255 caracteres
    otro_pregunta_16 = models.CharField(max_length=255, blank=True, null=True)

    # Pregunta 17: Respuesta final - máximo 255 caracteres
    pregunta_17 = models.CharField(max_length=255, blank=True, null=True)

    # === CAMPOS DE CONTROL Y METADATOS ===

    # Confirmación de envío de la encuesta - máximo 10 caracteres ('Si'/'No')
    confirmacion = models.CharField(max_length=10, blank=True, null=True)

    # URL de foto adjunta a la encuesta - máximo 255 caracteres
    foto_url = models.CharField(max_length=255, blank=True, null=True)

    # Estado de sincronización con el servidor (0=no, 1=sí)
    sincronizado = models.IntegerField(default=0)

    # Estado de completitud de la encuesta (0=incompleta, 1=completa)
    completada = models.IntegerField(default=0)

    # Timestamp de creación en formato string - máximo 100 caracteres
    created_at = models.CharField(max_length=100, blank=True, null=True)

    # Timestamp de última actualización en formato string - máximo 100 caracteres
    updated_at = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'EncuestasOffline'    # Tabla: EncuestasOffline
        ordering = ['-encuesta_ID']      # Ordenar por ID descendente
        verbose_name = "Encuesta Offline"

    def __str__(self):
        return f"Encuesta Offline {self.encuesta_ID} - {self.escuela}"


class EncuestasOnline(models.Model):
    """
    Modelo para almacenar encuestas realizadas directamente online.

    Complementa el sistema de encuestas offline permitiendo la captura
    directa de datos cuando hay conectividad disponible.
    """

    # Clave primaria autoincremental de la encuesta online
    encuesta_ID = models.AutoField(primary_key=True)

    # ID del usuario que realizó la encuesta - máximo 100 caracteres
    usuario_ID = models.CharField(max_length=100, blank=True, null=True)

    # UUID único para consistencia con sistema offline - máximo 100 caracteres
    f_uuid = models.CharField(blank=True, null=True, max_length=100)

    # Fecha de respuesta en formato string - máximo 100 caracteres
    fecha_respuesta = models.CharField(max_length=100, blank=True, null=True)

    # Estado de completitud de la encuesta (0=incompleta, 1=completa)
    completada = models.IntegerField(default=0)

    # Respuestas de la encuesta en formato texto/JSON
    respuestas = models.TextField(blank=True, null=True)

    # Referencia a la plantilla de encuesta utilizada
    encuesta_FK = models.ForeignKey('EncuestaModel', on_delete=models.CASCADE, verbose_name='encuesta')

    class Meta:
        db_table = 'encuestas_online'    # Tabla: encuestas_online
        ordering = ['-encuesta_ID']      # Ordenar por ID descendente
        verbose_name = "Encuesta Online"

    def __str__(self):
        return f"Encuesta {self.encuesta_ID} - Usuario {self.usuario_ID}"


class EncuestaModel(models.Model):
    """
    Modelo para definir plantillas/estructuras de encuestas.

    Define las encuestas disponibles en el sistema con sus preguntas
    y configuraciones específicas.
    """

    # Clave primaria autoincremental de la plantilla de encuesta
    encuesta_ID = models.AutoField(primary_key=True)

    # Nombre descriptivo de la encuesta - máximo 255 caracteres
    nombre = models.CharField(max_length=255, blank=True, null=True)

    # Descripción detallada del propósito de la encuesta
    descripcion = models.TextField(blank=True, null=True)

    # Fecha de creación en formato string - máximo 100 caracteres
    fecha_creacion = models.CharField(max_length=100, blank=True, null=True)

    # Estado de la encuesta - si está activa para ser utilizada (1=activa, 0=inactiva)
    activa = models.IntegerField(default=1)

    # Estructura de preguntas en formato JSON o texto plano
    preguntas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'encuesta'           # Tabla: encuesta
        ordering = ['-fecha_creacion']  # Ordenar por fecha de creación descendente
        verbose_name = "Encuesta"

    def __str__(self):
        return self.nombre

    def is_active(self):
        """
        Verifica si la encuesta está activa

        Returns:
            bool: True si la encuesta está activa
        """
        return self.activa == 1

    def activate(self):
        """
        Activa la encuesta para ser utilizada
        """
        self.activa = 1
        self.save()

    def deactivate(self):
        """
        Desactiva la encuesta
        """
        self.activa = 0
        self.save()
