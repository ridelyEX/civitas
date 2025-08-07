from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.db.models import AutoField
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
import uuid

from rest_framework.exceptions import ValidationError

class DesUrUsers(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=75, blank=True)
    password = models.CharField(max_length=128)
    bday = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='user_photos', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'desur_users'
        ordering = ['username']

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class DesUrLoginDate(models.Model):
    login_ID = models.AutoField(primary_key=True)
    user_FK = models.ForeignKey(DesUrUsers, on_delete=models.CASCADE, verbose_name='usuarios')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DesUrLoginDate'
        ordering = ['user_FK']

    def __str__(self):
        return str(self.date)

    @classmethod
    def create(cls, user):
        return cls.objects.create(
            user_FK=user
        )


class Uuid(models.Model):
    prime =  models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    class Meta:
        db_table: 'uuid'
        ordering = ["uuid"]

    def __str__(self):
        return str(self.uuid)


class data(models.Model):
    data_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="ides")
    nombre  = models.CharField(max_length=30, verbose_name="Nombre")
    pApe    = models.CharField(max_length=30, verbose_name="Apellido Paterno")
    mApe    = models.CharField(max_length=30, verbose_name="Apellido Materno")
    bDay    = models.DateField()
    asunto  = models.CharField(max_length=30)
    tel     = PhoneNumberField(region="MX")
    curp    = models.CharField(max_length=18)
    sexo    = models.CharField(max_length=10)
    dirr    = models.TextField()
    disc    = models.CharField(max_length=100, verbose_name="discapacidad")
    etnia   = models.CharField(max_length=100, verbose_name="etnia")
    vul     = models.CharField(max_length=100, verbose_name="vulnerabilidad")

    class Meta:
        db_table = 'dataT'
        get_latest_by = 'data_ID'
        ordering = ["data_ID"]
        verbose_name = "Datos"

    def __str__(self):
        return self.nombre

    #def save(self, *args, **kwargs):
     #   if not self.fuuid and Uuid.objects.exists():
      #      self.fuuid = Uuid.objects.latest('uuid')
       # super().save(*args, **kwargs)


class SubirDocs(models.Model):
    doc_ID = AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    nomDoc = models.CharField(max_length=50, null=True, blank=True)

    descDoc = models.CharField(max_length=100)
    doc = models.FileField(upload_to='documents/')
    fechaDoc = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'files'
        ordering = ['fechaDoc']
        verbose_name = "Documentos"

    def __str__(self):
        return self.nomDoc or "Documento sin nombre"


class soli(models.Model):
    soli_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="Datos")
    doc_ID = models.ForeignKey(SubirDocs, on_delete=models.CASCADE, verbose_name="Documentos",
                                blank=True, null=True)
    # Agregar referencia al empleado que procesó el trámite
    processed_by = models.ForeignKey(DesUrUsers, on_delete=models.CASCADE,
                                   verbose_name="Procesado por", null=True, blank=True)
    dirr   = models.TextField()
    calle = models.CharField(max_length=50, null=True, blank=True)
    colonia = models.CharField(max_length=50, null=True, blank=True)
    cp = models.CharField(max_length=5, null=True, blank=True)
    descc   = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    info   = models.TextField(blank=True, null=True)
    puo = models.CharField(max_length=50, null=True, blank=True)
    foto = models.ImageField(upload_to = 'fotos', null=True, blank=True)
    folio = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'soli'
        ordering = ["data_ID"]
        verbose_name = "Solicitud"

    def __str__(self):
        return str(self.soli_ID)

class Files(models.Model):
    fDoc_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    finalDoc = models.FileField(upload_to='solicitudes/')
    nomDoc = models.CharField(max_length=255, null=True, blank=True)
    soli_FK = models.ForeignKey(soli, on_delete=models.CASCADE)

    class Meta:
        db_table = 'solicitudes'
        ordering = ['fDoc_ID']
        verbose_name = "solicitudes"

    def __str__(self):
        return str(self.nomDoc)



class PpGeneral(models.Model):

    CHOICES_STATE = [
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('malo', 'Malo'),
    ]
    
    INSTALATION_CHOICES = [
        ('cfe', 'CFE'),
        ('agua', 'Agua'),
        ('drenaje', 'Drenaje'),
        ('impermeabilizacion', 'Impermeabilización'),
        ('climas', 'Climas'),
        ('alumbrado', 'Alumbrado'),
    ]

    pp_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE, verbose_name="ides")

    nombre_promovente = models.CharField(max_length=100, verbose_name="Nombre del Promovente", null=True, blank=True)
    telefono = PhoneNumberField(region="MX", verbose_name="Teléfono", null=True, blank=True)
    categoria = models.CharField(max_length=100, verbose_name="Categoria del Proyecto", null=True, blank=True)
    direccion_proyecto = models.TextField(verbose_name="Dirección del Proyecto", null=True, blank=True)
    calle_p = models.CharField(max_length=50, null=True, blank=True)
    colonia_p = models.CharField(max_length=50, null=True, blank=True)
    cp_p = models.CharField(max_length=5, null=True, blank=True)
    desc_p = models.TextField(verbose_name="Descripción del Proyecto", null=True, blank=True)
    fecha_pp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    #choices menu

    instalation_choices = models.JSONField(
        verbose_name="instalaciones",
        default=dict,
        null=True,
        blank=True,
        help_text="Seleccione las instalaciones necesarias para la propuesta.",
    )

    notas_importantes = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_general'
        ordering = ['pp_ID']
        verbose_name = "Propuesta General"

    def __str__(self):
        return self.nombre_promovente or "Propuesta sin nombre"

    def clean(self):
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

    notas_parque = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_parque'
        ordering = ['p_parque_ID']
        verbose_name = "Propuesta parque"

    def __str__(self):
        return str(self.p_parque_ID) or None



class PpEscuela(models.Model):
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

    notas_escuela = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_escuela'
        ordering = ['p_escuela_ID']
        verbose_name = "Propuesta Escuela"

    def __str__(self):
        return self.nom_escuela or None

class PpCS(models.Model):
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

    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)

    class Meta:
        db_table = 'pp_CS'
        ordering = ['p_cs_ID']
        verbose_name = "Propuesta Centro comunitario"

    def __str__(self):
        return str(self.p_cs_ID) or None

class PpInfraestructura(models.Model):
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
    pavimentacion_rehabilitacion = models.BooleanField(verbose_name="Rehabilitación", default=False)

    # Campos para Señalamiento Vial
    señalamiento_pintura = models.BooleanField(verbose_name="Pintura", default=False)
    señalamiento_señales = models.BooleanField(verbose_name="Señales verticales", default=False)

    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)


    class Meta:
        db_table = 'pp_infraestructura'
        ordering = ['pp_infraestructura_ID']
        verbose_name = "Propuesta Infraestructura"

    def __str__(self):
        return str(self.pp_infraestructura_ID) or None

class PpPluvial(models.Model):
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

    notas_propuesta = models.TextField(verbose_name="Notas Importantes", null=True, blank=True)


    class Meta:
        db_table = 'pp_pluvial'
        ordering = ['pp_pluvial_ID']
        verbose_name = "Propuesta Pluviales"

    def __str__(self):
        return str(self.pp_pluvial_ID) or None

class PpFiles(models.Model):
    fDoc_ID = models.AutoField(primary_key=True)
    fuuid = models.ForeignKey(Uuid, on_delete=models.CASCADE)
    fk_pp = models.ForeignKey(PpGeneral, on_delete=models.CASCADE, verbose_name="Propuesta General", null=True, blank=True)
    finalDoc = models.FileField(upload_to='pp_solicitudes/')
    nomDoc = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'pp_solicitudes'
        ordering = ['fDoc_ID']
        verbose_name = "solicitudes presupuesto participativo"

    def __str__(self):
        return str(self.nomDoc)


# Excel

class Pagos(models.Model):
    pago_ID = models.AutoField(primary_key=True)
    data_ID = models.ForeignKey(data, on_delete=models.CASCADE,
                                verbose_name="datos")
    fecha = models.DateTimeField(null = True, blank = True)
    pfm = models.CharField(max_length=80, null = True, blank = True)

    class Meta:
        db_table = 'pagos'
        ordering = ['pago_ID']

    def __str__(self):
        return self.pfm or ""

    def save(self, *args, **kwargs):
        if not self.data_ID_id and data.objects.exists():
            self.data_ID_id = data.objects.latest('data_ID').data_ID
        super().save(*args, **kwargs)

class Licitaciones(models.Model):
    licitacion_ID = models.AutoField(primary_key=True)
    fecha_limite = models.DateField(blank=True, null=True)
    no_licitacion = models.CharField(max_length=15, blank=True, null=True)
    desc_licitacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'licitaciones'
        ordering = ['no_licitacion']
        verbose_name = "Licitación"

    def __str__(self):
        return self.no_licitacion or "Licitación sin número"