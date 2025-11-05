"""
Modelos de datos para el sistema DesUr (Desarrollo Urbano)
Sistema de gestión de trámites ciudadanos y presupuesto participativo
"""
from django.db import models
from django.db.models import AutoField
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
import uuid

from rest_framework.exceptions import ValidationError

class Uuid(models.Model):
    """
    Modelo de identificadores únicos para sesiones y trámites
    Genera UUIDs únicos para cada proceso de trámite ciudadano
    """
    # Clave primaria autoincremental para referencia interna
    prime = models.AutoField(primary_key=True)

    # UUID único generado automáticamente para cada sesión/trámite
    # Se usa para rastrear el progreso de trámites ciudadanos
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    class Meta:
        db_table = 'uuid'  # Tabla: uuid
        ordering = ["uuid"]  # Ordenar por UUID

    def __str__(self):
        return str(self.uuid)


class data(models.Model):
    """
    Modelo principal de datos del ciudadano solicitante
    Almacena información personal y demográfica del ciudadano
    """
    # Clave primaria autoincremental del registro de ciudadano
    data_ID = models.AutoField(primary_key=True)

    # Relación con UUID de sesión - vincula ciudadano con su trámite
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="ides")

    # === DATOS PERSONALES BÁSICOS ===
    # Nombre(s) del ciudadano - máximo 30 caracteres
    nombre = models.CharField(max_length=30, verbose_name="Nombre")

    # Apellido paterno del ciudadano - máximo 30 caracteres
    pApe = models.CharField(max_length=30, verbose_name="Apellido Paterno")

    # Apellido materno del ciudadano - máximo 30 caracteres
    mApe = models.CharField(max_length=30, verbose_name="Apellido Materno")

    # Fecha de nacimiento del ciudadano - formato YYYY-MM-DD
    bDay = models.DateField()

    # === DATOS DE CONTACTO ===
    # Número telefónico con validación para región México
    tel = PhoneNumberField(region="MX")

    # === DATOS OFICIALES ===
    # CURP (Clave Única de Registro de Población) - 18 caracteres
    curp = models.CharField(max_length=18)

    # Sexo del ciudadano (M/F/Otro) - máximo 10 caracteres
    sexo = models.CharField(max_length=10)

    # === DATOS DEL TRÁMITE ===
    # Código del asunto/trámite solicitado (ej: DOP00001)
    asunto = models.CharField(max_length=30)

    # Dirección completa del ciudadano o del problema a atender
    dirr = models.TextField()

    # === DATOS DEMOGRÁFICOS Y SOCIALES ===
    # Tipo de discapacidad del ciudadano (si aplica)
    disc = models.CharField(max_length=100, verbose_name="discapacidad")

    # Grupo étnico al que pertenece el ciudadano
    etnia = models.CharField(max_length=100, verbose_name="etnia")

    # Grupo vulnerable al que pertenece (adulto mayor, menor de edad, etc.)
    vul = models.CharField(max_length=100, verbose_name="vulnerabilidad")

    class Meta:
        db_table = 'dataT'  # Tabla: dataT
        get_latest_by = 'data_ID'  # Obtener el más reciente por ID
        ordering = ["data_ID"]  # Ordenar por ID ascendente
        verbose_name = "Datos"

    def __str__(self):
        return self.nombre


class SubirDocs(models.Model):
    """
    Modelo de documentos adjuntos subidos por ciudadanos
    Almacena archivos PDF, imágenes y otros documentos de respaldo
    """
    # Clave primaria autoincremental del documento
    doc_ID = AutoField(primary_key=True)

    # Relación con UUID de sesión - vincula documento con trámite específico
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)

    # Nombre original del archivo subido - máximo 50 caracteres
    nomDoc = models.CharField(max_length=50, null=True, blank=True)

    # Descripción del contenido del documento - máximo 100 caracteres
    descDoc = models.CharField(max_length=100)

    # Archivo físico almacenado en carpeta 'documents/'
    doc = models.FileField(upload_to='documents/')

    # Fecha y hora de subida del documento - se asigna automáticamente
    fechaDoc = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'files'  # Tabla: files
        ordering = ['fechaDoc']  # Ordenar por fecha de subida
        verbose_name = "Documentos"

    def __str__(self):
        return self.nomDoc or "Documento sin nombre"


class soli(models.Model):
    """
    Modelo principal de solicitudes/trámites procesados
    Almacena los detalles específicos del trámite y su procesamiento
    """
    # Clave primaria autoincremental de la solicitud
    soli_ID = models.AutoField(primary_key=True)

    # Relación con datos del ciudadano - vincula solicitud con ciudadano
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE, verbose_name="Datos")

    # Relación con documentos adjuntos (opcional)
    doc_ID = models.ForeignKey(SubirDocs, on_delete=models.CASCADE, verbose_name="Documentos",
                              blank=True, null=True)

    # Usuario empleado que procesó el trámite - referencia al modelo unificado Users
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   verbose_name="Procesado por", null=True, blank=True)

    # === DATOS DE UBICACIÓN DEL PROBLEMA ===
    # Dirección completa donde se ubica el problema a resolver
    dirr = models.TextField()

    # Calle específica extraída de la dirección
    calle = models.CharField(max_length=100, null=True, blank=True)

    # Colonia específica extraída de la dirección
    colonia = models.CharField(max_length=100, null=True, blank=True)

    # Código postal de la ubicación - 5 dígitos
    cp = models.CharField(max_length=5, null=True, blank=True)

    # === DETALLES DEL TRÁMITE ===
    # Descripción detallada del problema o solicitud
    descc = models.TextField(blank=True, null=True)

    # Información adicional proporcionada por el ciudadano
    info = models.TextField(blank=True, null=True)

    # PUO (Proceso Unidad Operativa) - tipo de proceso (OFI, CRC, MEC, etc.)
    puo = models.CharField(max_length=50, null=True, blank=True)

    # Fotografía del problema reportado - almacenada en 'fotos/'
    foto = models.ImageField(upload_to='fotos', null=True, blank=True)

    # === CONTROL ADMINISTRATIVO ===
    # Folio único generado para el trámite (ej: GOP-OFI-00001-1234/25)
    folio = models.CharField(max_length=50, null=True, blank=True)

    # Fecha y hora de creación de la solicitud - se asigna automáticamente
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'soli'  # Tabla: soli
        ordering = ["data_ID"]  # Ordenar por ID de ciudadano
        verbose_name = "Solicitud"

    def __str__(self):
        return f"Solicitud {self.soli_ID} - {self.data_ID.nombre}"



# === MODELOS DE PRESUPUESTO PARTICIPATIVO ===

class PpGeneral(models.Model):
    """
    Modelo general de propuestas de presupuesto participativo
    Almacena datos básicos de proyectos propuestos por ciudadanos
    """
    # Opciones de estado para instalaciones existentes
    CHOICES_STATE = [
        ('bueno', 'Bueno'),           # Instalación en buen estado
        ('regular', 'Regular'),        # Instalación requiere mantenimiento menor
        ('malo', 'Malo'),             # Instalación requiere reparación mayor
        ('no existe', 'No existe'),   # Instalación no existe, requiere construcción
    ]

    # Tipos de instalaciones que se pueden evaluar
    INSTALATION_CHOICES = [
        ('cfe', 'CFE'),                              # Instalación eléctrica
        ('agua', 'Agua'),                            # Sistema de agua potable
        ('drenaje', 'Drenaje'),                      # Sistema de drenaje
        ('impermeabilizacion', 'Impermeabilización'), # Impermeabilización
        ('climas', 'Climas'),                        # Aires acondicionados
        ('alumbrado', 'Alumbrado'),                  # Alumbrado público
    ]

    # Clave primaria autoincremental de la propuesta
    pp_ID = models.AutoField(primary_key=True)

    # Relación con UUID de sesión - vincula propuesta con sesión
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="ides")

    # === DATOS DEL PROMOVENTE ===
    # Nombre completo de quien propone el proyecto
    nombre_promovente = models.CharField(max_length=100, verbose_name="Nombre del Promovente", null=True, blank=True)

    # Teléfono de contacto del promovente - validado para México
    telefono = PhoneNumberField(region="MX", verbose_name="Teléfono", null=True, blank=True)

    # === DATOS DEL PROYECTO ===
    # Categoría del proyecto (parque, escuela, infraestructura, etc.)
    categoria = models.CharField(max_length=100, verbose_name="Categoria del Proyecto", null=True, blank=True)

    # Dirección completa donde se realizará el proyecto
    direccion_proyecto = models.TextField(verbose_name="Dirección del Proyecto", null=True, blank=True)

    # === DESGLOSE DE DIRECCIÓN ===
    # Calle específica del proyecto
    calle_p = models.CharField(max_length=50, null=True, blank=True)

    # Colonia específica del proyecto
    colonia_p = models.CharField(max_length=50, null=True, blank=True)

    # Código postal del proyecto - 5 dígitos
    cp_p = models.CharField(max_length=5, null=True, blank=True)

    # Descripción detallada del proyecto propuesto
    desc_p = models.TextField(verbose_name="Descripción del Proyecto", null=True, blank=True)

    # Fecha y hora de creación de la propuesta - se asigna automáticamente
    fecha_pp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    # === EVALUACIÓN DE INSTALACIONES ===
    # Campo JSON que almacena el estado de diferentes instalaciones
    # Estructura: {"cfe": "bueno", "agua": "malo", "drenaje": "regular"}
    instalation_choices = models.JSONField(
        verbose_name="instalaciones",
        default=dict,  # Diccionario vacío por defecto
        null=True,
        blank=True,
        help_text="Seleccione las instalaciones necesarias para la propuesta.",
    )

    # Notas adicionales importantes sobre el proyecto
    notas_importantes = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_general'  # Tabla: pp_general
        ordering = ['pp_ID']  # Ordenar por ID de propuesta
        verbose_name = "Propuesta General"

    def __str__(self):
        return self.nombre_promovente or "Propuesta sin nombre"

    def clean(self):
        """Validación personalizada del campo JSON de instalaciones"""
        super().clean()
        valid_choices = [choice[0] for choice in self.INSTALATION_CHOICES]
        valid_states = [choice[0] for choice in self.CHOICES_STATE]

        if self.instalation_choices:
            for instalacion, estado in self.instalation_choices.items():
                if instalacion not in valid_choices:
                    raise ValidationError({
                        'instalation_choices': f"Instalación '{instalacion}' no es válida"
                    })
                if estado not in valid_states:
                    raise ValidationError({
                        'instalation_choices': f"Estado '{estado}' no es valido para '{instalacion}'"
                    })

class PpParque(models.Model):
    """
    Modelo para propuestas de parques en el presupuesto participativo
    Almacena detalles sobre canchas, alumbrado, juegos y equipamiento
    """

    # Campos para Cancha

    p_parque_ID = models.AutoField(primary_key=True)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)

    cancha_futbol_rapido = models.BooleanField(verbose_name="Fútbol Rápido", default=False)
    cancha_futbol_soccer = models.BooleanField(verbose_name="Fútbol Soccer", default=False)
    cancha_futbol_7x7 = models.BooleanField(verbose_name="Fútbol 7x7", default=False)
    cancha_beisbol = models.BooleanField(verbose_name="Beisbol", default=False)
    cancha_softbol = models.BooleanField(verbose_name="Softbol", default=False)
    cancha_usos_multiples = models.BooleanField(verbose_name="Usos Múltiples", default=False)
    cancha_otro = models.BooleanField(verbose_name="Otro tipo de cancha", default=False)

    # Campos para Alumbrado
    alumbrado_rehabilitacion = models.BooleanField(verbose_name="Rehabilitación de alumbrado", default=False)
    alumbrado_nuevo = models.BooleanField(verbose_name="Alumbrado nuevo", default=False)

    # Campos para Juegos
    juegos_dog_park = models.BooleanField(verbose_name="Dog park", default=False)
    juegos_infantiles = models.BooleanField(verbose_name="Juegos infantiles", default=False)
    juegos_ejercitadores = models.BooleanField(verbose_name="Ejercitadores", default=False)
    juegos_otro = models.BooleanField(verbose_name="Otro tipo de juegos", default=False)

    # Campos para Techumbre
    techumbre_domo = models.BooleanField(verbose_name="Domo", default=False)
    techumbre_kiosko = models.BooleanField(verbose_name="Techo tipo kiosko", default=False)

    # Campos para Equipamiento
    equipamiento_botes = models.BooleanField(verbose_name="Botes de basura", default=False)
    equipamiento_bancas = models.BooleanField(verbose_name="Bancas", default=False)
    equipamiento_andadores = models.BooleanField(verbose_name="Andadores", default=False)
    equipamiento_rampas = models.BooleanField(verbose_name="Rampas", default=False)

    # Notas adicionales sobre la propuesta de parque
    notas_parque = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_parque'
        ordering = ['p_parque_ID']
        verbose_name = "Propuesta parque"

    def __str__(self):
        return str(self.p_parque_ID) or None



class PpEscuela(models.Model):
    """
    Modelo para propuestas de rehabilitación o construcción de escuelas
    Almacena detalles sobre salones, baños, electricidad y construcción nueva
    """

    # Campos para Rehabilitación

    p_escuela_ID = models.AutoField(primary_key=True)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)

    nom_escuela = models.CharField(max_length=100, verbose_name="Nombre de la Escuela", null=True, blank=True)

    rehabilitacion_baños = models.BooleanField(verbose_name="Baños", default=False)
    rehabilitacion_salones = models.BooleanField(verbose_name="Salones", default=False)
    rehabilitacion_electricidad = models.BooleanField(verbose_name="Instalación eléctrica", default=False)
    rehabilitacion_gimnasio = models.BooleanField(verbose_name="Gimnasio", default=False)
    rehabilitacion_otro = models.BooleanField(verbose_name="Otro tipo de rehabilitación", default=False)

    # Campos para Construcción Nueva
    construccion_domo = models.BooleanField(verbose_name="Domo", default=False)
    construccion_aula = models.BooleanField(verbose_name="Aula", default=False)

    # Campos para Cancha
    cancha_futbol_rapido = models.BooleanField(verbose_name="Fútbol Rápido", default=False)
    cancha_futbol_7x7 = models.BooleanField(verbose_name="Fútbol 7x7", default=False)
    cancha_usos_multiples = models.BooleanField(verbose_name="Usos Múltiples", default=False)

    # Notas adicionales sobre la propuesta de escuela
    notas_escuela = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_escuela'
        ordering = ['p_escuela_ID']
        verbose_name = "Propuesta Escuela"

    def __str__(self):
        return self.nom_escuela or None

class PpCS(models.Model):
    """
    Modelo para propuestas de rehabilitación o construcción de centros comunitarios
    Almacena detalles sobre salones, baños, electricidad y construcción nueva
    """

    # Campos para Rehabilitación

    p_cs_ID = models.AutoField(primary_key=True)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)

    rehabilitacion_baños = models.BooleanField(verbose_name="Baños", default=False)
    rehabilitacion_salones = models.BooleanField(verbose_name="Salones", default=False)
    rehabilitacion_electricidad = models.BooleanField(verbose_name="Instalación eléctrica", default=False)
    rehabilitacion_gimnasio = models.BooleanField(verbose_name="Gimnasio", default=False)

    # Campos para Construcción Nueva
    construccion_salon = models.BooleanField(verbose_name="Salón", default=False)
    construccion_domo = models.BooleanField(verbose_name="Domo", default=False)
    construccion_otro = models.BooleanField(verbose_name="Otro tipo de construcción", default=False)

    # Notas adicionales sobre la propuesta de centro comunitario
    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_CS'
        ordering = ['p_cs_ID']
        verbose_name = "Propuesta Centro comunitario"

    def __str__(self):
        return str(self.p_cs_ID) or None

class PpInfraestructura(models.Model):
    """
    Modelo para propuestas de infraestructura urbana
    Almacena detalles sobre bardas, muros, pavimentación y señalamiento vial
    """

    # Campos para Infraestructura

    pp_infraestructura_ID = models.AutoField(primary_key=True)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)

    infraestructura_barda = models.BooleanField(verbose_name="Barda perimetral", default=False)
    infraestructura_banquetas = models.BooleanField(verbose_name="Banquetas", default=False)
    infraestructura_muro = models.BooleanField(verbose_name="Muro de contención", default=False)
    infraestructura_camellon = models.BooleanField(verbose_name="Intervención en camellón", default=False)
    infraestructura_crucero = models.BooleanField(verbose_name="Crucero seguro / cruce peatonal", default=False)
    infraestructura_ordenamiento = models.BooleanField(verbose_name="Ordenamiento vehicular en calle", default=False)
    infraestructura_er = models.BooleanField(verbose_name="Escalinatas / rampas", default=False)
    infraestructura_mejora = models.BooleanField(verbose_name="Mejoramiento de imagen vehicular (pintura)", default=False)
    infraestructura_peatonal = models.BooleanField(verbose_name="Paso peatonal", default=False)
    infraestructura_bayoneta = models.BooleanField(verbose_name="Bayoneta / retorno", default=False)
    infraestructura_topes = models.BooleanField(verbose_name="Pasos pompeyanos / reductores de velocidad", default=False)
    infraestructura_puente = models.BooleanField(verbose_name="Puente vehicular", default=False)

    # Campos para Pavimentación
    pavimentacion_asfalto = models.BooleanField(verbose_name="Asfalto", default=False)
    pavimentacion_concreto = models.BooleanField(verbose_name="hidraulico", default=False)
    pavimentacion_rehabilitacion = models.BooleanField(verbose_name="Rehabilitación", default=False)

    # Campos para Señalamiento Vial
    señalamiento_pintura = models.BooleanField(verbose_name="Pintura", default=False)
    señalamiento_señales = models.BooleanField(verbose_name="Señales verticales", default=False)

    # Notas adicionales sobre la propuesta de infraestructura
    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)


    class Meta:
        db_table = 'pp_infraestructura'
        ordering = ['pp_infraestructura_ID']
        verbose_name = "Propuesta Infraestructura"

    def __str__(self):
        return str(self.pp_infraestructura_ID) or None

class PpPluvial(models.Model):
    """
    Modelo para propuestas de soluciones pluviales
    Almacena detalles sobre muros de contención, canalización y puentes peatonales
    """

    # Campos para Soluciones Pluviales

    pp_pluvial_ID = models.AutoField(primary_key=True)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)

    pluvial_muro_contencion = models.BooleanField(verbose_name="Muro de contención", default=False)
    pluvial_canalizacion = models.BooleanField(verbose_name="Canalización de arroyo", default=False)
    pluvial_puente_peatonal = models.BooleanField(verbose_name="Puente peatonal sobre arroyo", default=False)
    pluvial_vado = models.BooleanField(verbose_name="Construcción de vado", default=False)
    pluvial_puente = models.BooleanField(verbose_name="Puente", default=False)
    pluvial_desalojo = models.BooleanField(verbose_name="Solución de desalojo pluvial / descargas pluviales", default=False)
    pluvial_rejillas = models.BooleanField(verbose_name="Rejillas pluviales", default=False)
    pluvial_lavaderos = models.BooleanField(verbose_name="Lavaderos (para evitar socavación / inundaciones)", default=False)
    pluvial_obra_hidraulica = models.BooleanField(verbose_name="Rehabilitación de obra hidráulica", default=False)
    pluvial_reposicion_piso = models.BooleanField(verbose_name="Reposición de piso de arroyo", default=False)
    pluvial_proteccion_inundaciones = models.BooleanField(verbose_name="Protección contra inundaciones", default=False)
    pluvial_otro = models.BooleanField(verbose_name="Otro", default=False)

    # Notas adicionales sobre la propuesta de soluciones pluviales
    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)


    class Meta:
        db_table = 'pp_pluvial'
        ordering = ['pp_pluvial_ID']
        verbose_name = "Propuesta Pluviales"

    def __str__(self):
        return str(self.pp_pluvial_ID) or None


class Files(models.Model):
    """
    Modelo de archivos finales generados por el sistema
    Almacena PDFs oficiales y documentos generados automáticamente
    """
    # Clave primaria autoincremental del archivo final
    fDoc_ID = models.AutoField(primary_key=True)

    # Nombre del documento final generado
    nomDoc = models.CharField(max_length=200, verbose_name="Nombre del documento")

    # Relación con UUID de sesión - vincula archivo con trámite
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="UUID")

    # Relación con solicitud específica (opcional)
    soli_FK = models.ForeignKey(soli, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Solicitud")

    # Relación con propuesta de presupuesto participativo (opcional)
    pp_FK = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name="Presupuesto Participativo")

    # Archivo PDF final generado - almacenado en 'documents/'
    finalDoc = models.FileField(upload_to='documents/', verbose_name="Documento final")

    class Meta:
        db_table = 'solicitudes'  # Tabla: solicitudes
        ordering = ['fDoc_ID']  # Ordenar por ID de archivo
        verbose_name = "solicitudes"

    def __str__(self):
        return str(self.nomDoc)

class Pagos(models.Model):
    """
    Modelo para el registro de pagos realizados por los ciudadanos
    Almacena información sobre el monto, fecha y método de pago
    """
    pago_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="datos")

    # Fecha y hora del pago - puede ser nulo
    fecha = models.DateTimeField(null = True, blank = True)

    # Método de pago (PFM) - descripción del método utilizado
    pfm = models.CharField(max_length=80, null = True, blank = True)

    class Meta:
        db_table = 'pagos'
        ordering = ['pago_ID']

    def __str__(self):
        return self.pfm or ""

    def save(self, *args, **kwargs):
        """Asignar automáticamente el último dato si no se proporciona"""
        if not self.data_ID_id and data.objects.exists():
            self.data_ID = data.objects.latest('data_ID')
        super().save(*args, **kwargs)
