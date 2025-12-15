"""
Vista principal de DesUr - Sistema de trámites de Desarrollo Urbano
Maneja todas las operaciones relacionadas con solicitudes ciudadanas, documentos y presupuesto participativo
"""
import base64
import uuid
from io import BytesIO
import re
import json
import logging
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .WSDService import WsDomicilios
from .WsConfig import WSDConfig
from .services import LocalGISService

# Imports para PDF (weasyprint)
try:
    from weasyprint import HTML
except ImportError:
    # Si weasyprint no está disponible, crear un mock
    class HTML:
        def __init__(self, **kwargs):
            pass
        def write_pdf(self, target=None):
            return b"PDF content not available"

# Usar el modelo unificado de usuarios de CMIN
from portaldu.cmin.models import Users, LoginDate, Licitaciones

# Imports de modelos locales de DesUr
from .models import (data, soli, Files, Uuid,
                     PpCS, PpEscuela, PpGeneral, PpPluvial, PpParque, PpInfraestructura,
                     SubirDocs, Pagos)
from .forms import (GeneralRender, CsRender, EscuelaRender, PluvialRender, ParqueRender,
                    DesUrLogin, InfraestructuraRender)

# Logger para registro de eventos y errores del módulo
logger = logging.getLogger(__name__)

# Decorador personalizado para validar acceso a DesUr
def desur_access_required(view_func):
    """
    Decorador que verifica que el usuario tenga acceso a DesUr basado en su rol

    Args:
        view_func: Función de vista a proteger

    Returns:
        Función wrapper que valida permisos antes de ejecutar la vista

    Behavior:
        - Redirige a login si el usuario no está autenticado
        - Redirige a menú CMIN si el usuario tiene acceso CMIN pero no DesUr
        - Muestra mensaje de error si el usuario no tiene permisos
    """
    def wrapper(request, *args, **kwargs):
        # Validar autenticación del usuario
        if not request.user.is_authenticated:
            return redirect('login')  # Redirigir al login unificado

        # Validar permisos específicos de DesUr según rol del usuario
        if not request.user.has_desur_access():
            messages.error(request, "No tienes permisos para acceder a esta sección")
            # Si tiene acceso a CMIN, redirigir ahí, sino al login
            if request.user.has_cmin_access():
                return redirect('menu')
            else:
                return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper

def test_views(request):
    return render(request, 'ds.html')

def desur_logout_view(request):
    """
    Vista de logout de DesUr - ahora usa el logout unificado

    Note:
        Mantiene compatibilidad con URLs antiguas pero usa el sistema central
    """
    return redirect('logout')

def custom_handler_404(request, exception):
    """
    Manejo de error 404 personalizado para AGEO.

    Args:
        request (HttpRequest): Objeto de la solicitud HTTP.
        exception (Exception): Excepción capturada

    Return:
        HttpResponse: Página personalizada de error 404
    """

    logger.warning(f"404 Error: {request.path} - User: {request.user}")

    context = {
        'is_authenticated': request.user.is_authenticated,
        'error_path': request.path,
        'home_url': None,
        'module': None,
        'user_role': None,
        'exception': str(exception) if exception else 'Página no encontrada',
    }

    if request.user.is_authenticated:
        if request.path.startswith('/ageo/'):
            context['module'] = 'ageo'
            context['home_url'] = 'home'
            context['user_role'] = getattr(request.user, 'rol', 'usuario')
        elif request.path.startswith('/cmin/'):
            context['module'] = 'cmin'
            context['home_url'] = 'menu'
            context['user_role'] = getattr(request.user, 'rol', 'usuario')
        else:
            context['home_url'] = 'menu' if hasattr(request.user, 'has_cmin_access') and request.user.has_cmin_access() else 'home'
    else:
        context['home_url'] = 'login_view'
        context['module'] = 'cmin'

    return render(request, '404_template/404_template.html', context, status=404)

def test_404(request):
    from django.http import Http404
    raise Http404('Página de prueba 404 ')

# Vistas del sistema de trámites requieren autenticación
# Solo empleados/funcionarios autorizados pueden operar el sistema

@login_required
@desur_access_required
def base(request):
    """
    Vista base para confirmar guardado de documentos

    Args:
        request: HttpRequest con cookie de UUID de sesión

    Returns:
        HttpResponse con confirmación o redirección si no hay UUID

    Note:
        Requiere UUID válido en cookies para mostrar confirmación

    Template:
        documet/save.html
    """
    # Obtener UUID de sesión de trabajo desde cookies
    uuid = request.COOKIES.get('uuid')

    # Si no hay UUID, redirigir al menú (sesión inválida)
    if not uuid:
        return redirect('home')  # Corregir redirección
    return render(request, 'documet/save.html',{'uuid':uuid})

@login_required
@desur_access_required
def home(request):
    """
    Punto de entrada para iniciar un nuevo trámite - Selección de tipo de trámite

    Args:
        request: HttpRequest con selección de tipo de trámite (POST)

    Returns:
        HttpResponse con opciones o redirección según selección

    Actions:
        - op: Obra pública (redirige a captura de datos del ciudadano)
        - pp: Presupuesto participativo (redirige a formulario general PP)

    Side Effects:
        - Crea o valida UUID de sesión
        - Establece cookie 'uuid' con duración de 1 hora

    Cookie Management:
        - uuid: Identificador único de sesión de trabajo (1 hora de duración)

    Template:
        main.html
    """

    logger.debug(f"Método: {request.method}")
    logger.debug(f"POST data: {request.POST}")
    logger.debug(f"Cookie UUID: {request.COOKIES.get('uuid')}")

    if request.method == 'POST':
        # Obtener UUID de sesión existente
        uuidM = request.COOKIES.get('uuid')
        action = request.POST.get('action')
        logger.debug(f"Acción seleccionada: {action}")

        if not action or action not in ['op', 'pp']:
            messages.error(request, "selecciona un tipo de trámite")
            return render(request, 'main.html')

        # Generar nuevo UUID si no existe
        if uuidM:
            uuid_obj = Uuid.objects.filter(uuid=uuidM).first()
            if not uuid_obj:
                uuid_obj = Uuid.objects.create(uuid=uuidM)
                logger.info(f"uuid recreado en BD")
        else:
            uuidM = str(uuid.uuid4())
            uuid_obj = Uuid.objects.create(uuid=uuidM)
            logger.info(f"uuid recreado en BD")

        # Redirigir según el tipo de acción seleccionado
        if action == 'op':
            response = redirect('data')
        elif action == 'pp':
            response = redirect('general')
        else:
            response = redirect('home')  # Corregir redirección

        # Establecer cookie con UUID de sesión
        response.set_cookie('uuid', uuidM, max_age=3600)
        return response
    return render(request, 'main.html')

@login_required
@desur_access_required
def intData(request):
    """
    Captura de datos personales del ciudadano que solicita el trámite

    Args:
        request: HttpRequest con datos del formulario ciudadano (POST) o petición inicial (GET)

    Returns:
        HttpResponse con formulario o redirección según proceso

    Context (GET):
        - dir: Dirección precargada (opcional)
        - asunto: Tipo de asunto/trámite
        - uuid: UUID de sesión
        - local_gis_enabled: Estado del servicio GIS local (desactivado temporalmente)

    Form Fields (POST):
        - nombre: Nombre del ciudadano (obligatorio, uppercase)
        - pApe: Apellido paterno (obligatorio, uppercase)
        - mApe: Apellido materno (obligatorio, uppercase)
        - bDay: Fecha de nacimiento (obligatorio, formato YYYY-MM-DD)
        - tel: Teléfono de contacto (obligatorio, 10-15 dígitos)
        - curp: CURP (obligatorio, validación de formato)
        - sexo: Género (obligatorio, valores: mujer/hombre)
        - dir: Dirección completa (obligatorio, min 10 caracteres)
        - asunto: Código del trámite (DOP00001-DOP00013)
        - etnia: Pertenencia a grupo étnico (opcional)
        - discapacidad: Tipo de discapacidad si aplica (opcional)
        - vulnerables: Pertenencia a grupo vulnerable (opcional)

    Context:
        - dir: Dirección del problema/solicitud
        - asunto: Código del tipo de trámite
        - asunto_desc: Descripción legible del trámite
        - puo: Tipo de proceso (origen de la solicitud)
        - datos: Datos personales del ciudadano (objeto data)
        - uuid: UUID de sesión
        - is_mobile/is_tablet/is_pc: Detección de tipo de dispositivo para UI responsiva
        - soli: Solicitudes previas del mismo ciudadano
        - local_gis_enabled: Estado del servicio GIS
        - fecha: Fecha actual del sistema

    Asuntos (Códigos DOP):
        - DOP00001: Arreglo de terracería
        - DOP00002: Bacheo de calles
        - DOP00003: Limpieza de arroyos al sur
        - DOP00004: Mantenimiento de rejillas pluviales
        - DOP00005: Pago de licitaciones
        - DOP00006: Rehabilitación de calles
        - DOP00007: Retiro de escombro
        - DOP00008: Solicitud de material caliche/fresado
        - DOP00009: Pavimentación de calles
        - DOP00010: Reductores de velocidad
        - DOP00011: Pintura para señalamientos
        - DOP00012: Arreglo de derrumbes de bardas
        - DOP00013: Tapiado

    Validation:
        Usa validar_datos() para validación robusta de todos los campos

    Redirects:
        - DOP00005: Redirige a captura de pago de licitación
        - Otros: Redirige a captura de solicitud

    Side Effects:
        - Crea o actualiza registro en modelo 'data'
        - Guarda 'asunto' en session para uso posterior

    Template:
        di.html
    """
    # Obtener dirección precargada desde query string
    direccion = request.GET.get('dir', '')
    # Obtener UUID de sesión de trabajo
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    colonias_wsd = []

    logger.debug("Procesando datos de ciudadano")

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
    except Uuid.DoesNotExist:
        logger.warning(f"UUID no encontrado: {uuid}")
        return redirect('home')

    asunto = ''

    if request.method == 'POST':
        errors = validar_datos(request.POST)
        if errors:
            return render(request, 'di.html', {
                'errors': errors,
                'datos': request.POST,
                'dir': direccion,
                'uuid': uuid,
            })

        try:
            with transaction.atomic():
                asunto = request.POST.get('asunto')
                request.session['asunto'] = asunto

                datos_persona = {
                    'nombre': request.POST.get('nombre').upper(),
                    'pApe': request.POST.get('pApe').upper(),
                    'mApe': request.POST.get('mApe').upper(),
                    'bDay': request.POST.get('bDay'),
                    'tel': request.POST.get('tel'),
                    'curp': request.POST.get('curp').upper(),
                    'sexo': request.POST.get('sexo'),
                    'dirr': request.POST.get('dir'),
                    'asunto': asunto,
                    'etnia': request.POST.get('etnia', 'No pertenece a una etnia'),
                    'disc': request.POST.get('discapacidad', 'sin discapacidad'),
                    'vul': request.POST.get('vulnerables', 'No pertenece a un grupo vulnerable'),
                }

                logger.info("Datos de ciudadano procesados correctamente")

                data.objects.update_or_create(
                    fuuid=uid,
                    defaults=datos_persona
                )

                match asunto:
                    case "DOP00005":
                        return redirect('pago')
                    case _:
                        return redirect('soli')

        except Exception as e:
            logger.error(f"Error al procesar datos: {str(e)}")
            return HttpResponse('Error al procesar los datos. Vuelva a intentarlo.')

    # Comentar las referencias a LocalGISService hasta que esté definido
    context = {
        'dir': direccion,
        'asunto': asunto,
        'uuid': uuid,
        'local_gis_enabled': False,  # Desactivar temporalmente
        # 'gis_services': LocalGISService.SERVICES,
        # 'service_status': service_status,
    }
    return render(request, 'di.html', context)


@login_required
@desur_access_required
def soliData(request):
    """
    Captura de solicitud de trámite con detalles específicos y documentación

    Args:
        request: HttpRequest con datos de la solicitud (POST) o petición inicial (GET)

    Returns:
        HttpResponse con formulario de solicitud o procesamiento de datos

    Context:
        - dir: Dirección del problema/solicitud
        - asunto: Código del tipo de trámite
        - asunto_desc: Descripción legible del trámite
        - puo: Tipo de proceso (origen de la solicitud)
        - datos: Datos personales del ciudadano (objeto data)
        - uuid: UUID de sesión
        - is_mobile/is_tablet/is_pc: Detección de tipo de dispositivo para UI responsiva
        - soli: Solicitudes previas del mismo ciudadano
        - local_gis_enabled: Estado del servicio GIS
        - fecha: Fecha actual del sistema

    Asuntos (Códigos DOP):
        - DOP00001: Arreglo de terracería
        - DOP00002: Bacheo de calles
        - DOP00003: Limpieza de arroyos al sur
        - DOP00004: Mantenimiento de rejillas pluviales
        - DOP00005: Pago de licitaciones
        - DOP00006: Rehabilitación de calles
        - DOP00007: Retiro de escombro
        - DOP00008: Solicitud de material caliche/fresado
        - DOP00009: Pavimentación de calles
        - DOP00010: Reductores de velocidad
        - DOP00011: Pintura para señalamientos
        - DOP00012: Arreglo de derrumbes de bardas
        - DOP00013: Tapiado

    Device Detection:
        Detecta tipo de dispositivo para adaptar interfaz (móvil/tablet/PC)

    Side Effects:
        - Si POST: Procesa solicitud completa con soli_processed()
        - Guarda PUO en session

    Template:
        ds.html
    """
    # SÍ login_required - empleados procesan solicitudes de ciudadanos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)

        is_mobile = request.user_agent.is_mobile
        is_tablet = request.user_agent.is_tablet
        is_pc = request.user_agent.is_pc

        logger.debug("Detectando tipo de dispositivo para interfaz")

        dir = request.GET.get('dir', '')
        asunto = request.session.get('asunto', '')
        print(asunto)
        puo = request.POST.get('puo', '')
        fecha = date.today()
        print(fecha)

        asunto_desc = asunto

        match asunto:
            case "DOP00001":
                asunto_desc = "ARREGLO DE TERRACERÍA"
            case "DOP00002":
                asunto_desc = "BACHEO DE CALLES"
            case "DOP00003":
                asunto_desc = "LIMPIEZA DE ARROYOS AL SUR DE LA CIUDAD"
            case "DOP00004":
                asunto_desc = "LIMPIEZA O MANTENIMIENTO DE REJILLAS PLUVIALES"
            case "DOP00005":
                asunto_desc = "PAGO DE COSTO POR PARTICIPACIÓN EN LICITACIONES DE OBRA PÚBLICA"
            case "DOP00006":
                asunto_desc = "REHABILITACIÓN DE CALLES"
            case "DOP00007":
                asunto_desc = "RETIRO DE ESCOMBRO Y MATERIAL DE ARRASTRE"
            case "DOP00008":
                asunto_desc = "SOLICITUD DE MATERIAL CALICHE/FRESADO"
            case "DOP00009":
                asunto_desc = "SOLICITUD DE PAVIMENTACIÓN DE CALLES"
            case "DOP00010":
                asunto_desc = "SOLICITUD DE REDUCTORES DE VELOCIDAD"
            case "DOP00011":
                asunto_desc = "SOLICITUD DE PINTURA PARA SEÑALAMIENTOS VIALES"
            case "DOP00012":
                asunto_desc = "AREGLO DE DERRUMBES DE BARDAS"
            case "DOP00013":
                asunto_desc = "TAPIADO"

        print(asunto_desc)

        dp = data.objects.select_related('fuuid').filter(fuuid=uid).first()
        if not dp:
            return redirect('home')

        if request.method == 'POST':
            return soli_processed(request, uid, dp)

        solicitud = soli.objects.filter(data_ID=dp).select_related('data_ID')

        # Comentar el uso de LocalGISService hasta que esté definido
        service_status = None #LocalGISService.get_service_status()

        context = {
            'dir': dir,
            'asunto': asunto,
            'asunto_desc': asunto_desc,
            'puo': puo,
            'datos': dp,
            'uuid': uuid,
            'is_mobile': is_mobile,
            'is_tablet': is_tablet,
            'is_pc': is_pc,
            'soli': solicitud,
            'local_gis_enabled': False,  # Desactivar temporalmente
            # 'gis_services': LocalGISService.SERVICES,
            # 'service_status': service_status,
            'fecha': fecha,
        }

        return render(request, 'ds.html', context)
    except Exception as e:
        return user_errors(request, e)

@login_required
@desur_access_required
def doc(request):
    """
    Vista de confirmación antes de generar o guardar documento final del trámite

    Args:
        request: HttpRequest con acción seleccionada (POST) o vista inicial (GET)

    Returns:
        HttpResponse con opciones o redirección según acción

    Actions (POST):
        - guardar: Guarda documento en base de datos
        - descargar: Genera PDF para descarga inmediata

    Context:
        - asunto: Código del tipo de trámite
        - datos: Datos personales del ciudadano
        - uuid: UUID de sesión

    Redirects:
        - DOP00005 + guardar: clear (limpiar sesión)
        - DOP00005 + descargar: document2 (documento de pago)
        - Otros + guardar: saveD1 (guardar documento general)
        - Otros + descargar: document (generar PDF general)

    Template:
        dg.html
    """
    # SÍ login_required - empleados gestionan documentación
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = data.objects.filter(fuuid__uuid=uuid).first()
    if not datos:
        return HttpResponse("No hay datos disponibles")

    asunto = request.session.get('asunto','')
    logger.debug("Procesando documentación")

    if asunto == "DOP00005":
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'guardar':
                return redirect('clear')
            elif action == 'descargar':
                return redirect ('document2')
    else:
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'guardar':
                return redirect('saveD1')
            elif action == 'descargar':
                return redirect('document')

    context = {'asunto': asunto,
               'datos':datos,
               'uuid':uuid}
    return render(request, 'dg.html', context)

@login_required
@desur_access_required
def dell(request, id):
    """
    Eliminar documento adjunto por ID de forma segura con validación de sesión

    Args:
        request: HttpRequest con método POST
        id: ID del documento SubirDocs a eliminar

    Returns:
        JsonResponse con resultado de la operación

    Response Format:
        Success: {'success': True}
        Error: {'error': 'mensaje de error'}

    Security:
        - Solo permite eliminación si el documento pertenece a la sesión UUID actual
        - Requiere método POST para prevenir eliminación accidental
        - Usuario debe estar autenticado y con permisos DesUr

    HTTP Methods:
        - POST: Elimina el documento
        - Other: Retorna error 405

    Status Codes:
        - 200: Eliminación exitosa
        - 405: Método no permitido
        - 500: Error en servidor
    """
    # SÍ login_required - empleados eliminan documentos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')
    if request.method == 'POST':
        try:
            docc = get_object_or_404(SubirDocs, pk=id, fuuid__uuid=uuid)
            docc.delete()
            logger.info("Documento eliminado correctamente")
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error eliminando documento: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método inválido'}, status=405)

@login_required
@desur_access_required
def docs(request):
    """
    Lista de documentos adjuntos del ciudadano en la sesión actual

    Args:
        request: HttpRequest con UUID en cookies

    Returns:
        HttpResponse con lista de documentos o redirección a captura de solicitud

    Context:
        - documentos: QuerySet de SubirDocs ordenados por nombre descendente
        - count: Cantidad total de documentos adjuntos
        - uuid: UUID de sesión actual

    Behavior:
        - GET: Muestra lista de documentos
        - POST: Redirige a captura de solicitud (continuar proceso)

    Template:
        docs.html
    """
    # SÍ login_required - empleados suben documentos del ciudadano
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')
    datos = get_object_or_404(Uuid, uuid=uuid)

    documentos = SubirDocs.objects.filter(fuuid=datos).order_by('-nomDoc')
    count = documentos.count()
    if request.method == 'POST':

        return redirect('soli')
    return render(request, 'docs.html',{
        'documentos':documentos,
        'count':count,
        'uuid':uuid,})


@login_required
@desur_access_required
def docs2(request):
    """
    Subir documento adjunto individual al trámite en proceso

    Args:
        request: HttpRequest con archivo y descripción (POST) o formulario (GET)

    Returns:
        JsonResponse si es AJAX, HttpResponse o redirect si es form normal

    Form Fields:
        - ffile: Archivo a subir (FILE, obligatorio)
        - descp: Descripción del documento (TEXT, obligatorio)

    Response (AJAX):
        {'success': True} si se guardó correctamente

    Side Effects:
        - Crea nuevo registro en SubirDocs
        - Guarda archivo físico en media/documents/

    Security:
        - Valida UUID de sesión
        - Requiere autenticación y permisos DesUr

    Template:
        docs2.html
    """
    # SÍ login_required - empleados gestionan documentos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')
    datos = get_object_or_404(Uuid, uuid=uuid)

    if request.method == 'POST' and request.FILES['ffile']:
        descDoc = request.POST.get('descp')
        docc = request.FILES.get('ffile')
        nomDoc = docc.name
        documento = SubirDocs(descDoc=descDoc, doc=docc, nomDoc=nomDoc, fuuid=datos)
        documento.save()

        if request.headers.get('xrequested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            return redirect('docs')
    else:
        return render(request, 'docs2.html')


#@desur_login_required
def pago(request):
    """
    Captura de información de pago para licitaciones de obra pública (DOP00005)

    Args:
        request: HttpRequest con datos del pago (POST) o formulario (GET)

    Returns:
        HttpResponse con formulario de licitaciones activas

    Context:
        - licitaciones: QuerySet de licitaciones activas (fecha_limite >= hoy)

    Form Fields (POST):
        - fecha: Fecha del pago realizado
        - pfm: Método de pago o forma de pago

    Side Effects:
        - Actualiza licitaciones vencidas (activa=False si fecha_limite < hoy)
        - Crea registro en modelo Pagos
        - Redirige a generación de documento

    Business Logic:
        Las licitaciones se marcan automáticamente como inactivas cuando su fecha límite pasa

    Template:
        pago.html
    """
    # SÍ login_required - empleados procesan pagos
   # uuid = request.COOKIES.get('uuid')
   # if not uuid:
   #    return redirect('home')
    #datos = get_object_or_404(data, fuuid__uuid=uuid)
    licitaciones = Licitaciones.objects.all()
    licitaciones.filter(
        fecha_limite__lt=timezone.now().date(),
        activa=True
    ).update(activa=False)
    licitaciones_activas = licitaciones.filter(activa=True).order_by('fecha_limite')

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        pfm = request.POST.get('pfm')
        pago = Pagos(fecha=fecha, pfm=pfm)
        pago.save()
        return redirect('doc')

    context = {
        "licitaciones": licitaciones_activas,
        #"datos": datos,
    }

    return render(request, 'pago.html', context)

@require_http_methods(["POST"])
def get_licitaciones(request):
    """
    Endpoint AJAX para obtener detalles de una licitación específica por ID

    Args:
        request: HttpRequest con JSON body conteniendo licitacion_ID

    Request Body:
        {'licitacion_ID': int}

    Returns:
        JsonResponse con datos de la licitación o error

    Response Format (Success):
        {
            'codigo': str,           # Número de licitación
            'descripcion': str,      # Descripción del proyecto
            'fecha': str            # Fecha límite formateada
        }

    Response Format (Error):
        {'error': 'Licitación no encontrada'}

    Status Codes:
        - 200: Licitación encontrada
        - 400: Licitación no existe

    HTTP Methods:
        Solo POST permitido (enforced por decorador)
    """
    data = json.loads(request.body)
    licitaciones_id = data.get('licitacion_ID')

    try:
        licitacion = Licitaciones.objects.get(licitacion_ID=licitaciones_id)
        return JsonResponse({
            'codigo': licitacion.no_licitacion,
            'descripcion': licitacion.desc_licitacion,
            'fecha': licitacion.fecha_limite.strftime('%d de %B, %Y') if licitacion.fecha_limite else '',
        })
    except Licitaciones.DoesNotExist:
        return JsonResponse({'error': 'Licitación no encontrada'}, status=400)


@login_required
@desur_access_required
def document(request):
    """
    Generar documento PDF del trámite para descarga inmediata (inline en navegador)

    Args:
        request: HttpRequest con UUID en cookies

    Returns:
        HttpResponse con PDF generado (Content-Type: application/pdf)

    PDF Content:
        - Datos personales del ciudadano
        - Detalles de la solicitud
        - Fotografía del problema
        - Documentos adjuntos
        - Folio generado automáticamente
        - Descripción del asunto/trámite

    Context para Template:
        - asunto: Descripción completa del trámite con código
        - datos: Diccionario con información personal del ciudadano
        - soli: Diccionario con detalles de la solicitud
        - puo: Texto descriptivo del proceso (origen)
        - documentos: Lista de documentos adjuntos
        - folio: Folio único generado para el trámite

    PDF Library:
        Usa WeasyPrint para renderizar HTML a PDF con estilos CSS

    Template:
        documet/document.html
    """
    # SÍ login_required - empleados generan documentos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = get_object_or_404(data, fuuid__uuid=uuid)
    #solicitud = get_object_or_404(soli, data_ID=datos)
    #ultima_solicitud = soli.objects.filter(data_ID=datos).last()
    try:
        ultima_solicitud = soli.objects.filter(data_ID=datos).latest('fecha')
    except soli.DoesNotExist:
        logger.error(request, "No hay solicitud")
        return redirect('soli')

    documentos = SubirDocs.objects.filter(fuuid__uuid=uuid)

    asunto = request.session.get('asunto', 'Sin asunto')
    puo = request.session.get('puo', 'Sin PUO')
    print(puo)

    uuid_obj = get_object_or_404(Uuid, uuid=uuid)

    if ultima_solicitud and ultima_solicitud.folio:
        puo_txt, _ = gen_folio(uuid_obj, ultima_solicitud.puo)
        folio = ultima_solicitud.folio
    else:
        puo_session = request.session.get('puo', 'general')
        puo_txt, folio = gen_folio(uuid_obj, puo_session)
    print(asunto)
    print(puo_txt)

    match asunto:
        case "DOP00001":
            asunto = "Arreglo de calles de terracería - DOP00001"
        case "DOP00002":
            asunto = "Bacheo de calles - DOP00002"
        case "DOP00003":
            asunto = "Limpieza de arroyos al sur de la ciudad - DOP00003"
        case "DOP00004":
            asunto = "Limpieza o mantenimiento de rejillas pluviales - DOP00004"
        case "DOP00005":
            asunto = "Pago de costo de participación en licitaciones de obra pública - DOP00005"
        case "DOP00006":
            asunto = "Rehabilitación de calles - DOP00006"
        case "DOP00007":
            asunto = "Retiro de escombro y material de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche/fresado - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de pintura para señalamientos viales - DOP00011"
        case "DOP00012":
            asunto = "Arreglo de derrumbe de bardas - DOP00012"
        case "DOP00013":
            asunto = "Tapiado - DOP00013"

    context = {
        "asunto": asunto,
        "datos": {
            "nombre": datos.nombre,
            "pApe": datos.pApe,
            "mApe": datos.mApe,
            "bDay": datos.bDay,
            "tel": datos.tel,
            "curp": datos.curp,
            "sexo": datos.sexo,
            "dir": datos.dirr,
            "disc":datos.disc,
            "etnia":datos.etnia,
            "vul": datos.vul if datos.vul else "No pertenece a un grupo vulnerable",
        },
        "soli": {
            "dir": ultima_solicitud.dirr if ultima_solicitud else "",
            "info": ultima_solicitud.info,
            "descc": ultima_solicitud.descc if ultima_solicitud else "",
            "foto": ultima_solicitud.foto,
            "fecha": ultima_solicitud.fecha,
        },
        'puo':puo_txt,
        'documentos':documentos,
        'folio': folio,
    }

    html = render_to_string("documet/document.html", context)
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/'))
    final_pdf = pdf_out.write_pdf()
    response = HttpResponse(final_pdf, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=información_general.pdf"
    return response


    #return render(request, "documet/document.html", context)


@login_required
@desur_access_required
def save_document(request):
    """
    Guardar documento PDF del trámite en base de datos para archivo permanente

    Args:
        request: HttpRequest con UUID en cookies

    Returns:
        HttpResponse con confirmación de documento guardado

    Process:
        1. Obtiene datos del ciudadano y solicitud
        2. Procesa documentos temporales en base64 desde formulario
        3. Genera folio si no existe
        4. Renderiza template HTML con contexto completo
        5. Convierte HTML a PDF usando WeasyPrint
        6. Guarda PDF en modelo Files asociado a la solicitud
        7. Muestra confirmación con link al documento

    Document Processing:
        - Lee documentos temporales en formato base64 del POST
        - Decodifica y guarda cada documento en SubirDocs
        - Valida formato JSON de cada documento temporal

    Naming Convention:
        Archivo: 'VS_{asunto}_{nombre}_{apellido}.pdf'

    Side Effects:
        - Crea registros en SubirDocs para documentos temporales
        - Crea registro en Files con PDF final
        - Guarda archivo físico en media/documents/

    Context:
        Similar a document() pero guarda en BD en lugar de descargar

    Template:
        documet/save.html (confirmación)
        documet/document.html (para renderizar PDF)
    """
    # SÍ login_required - empleados guardan documentos oficiales
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = get_object_or_404(data, fuuid__uuid=uuid)
    uid = get_object_or_404(Uuid, uuid=uuid)
    #solicitud = get_object_or_404(soli, data_ID=datos)
    #solicitud = soli.objects.filter(data_ID=datos).select_related('data_ID')

    try:
        solicitud = soli.objects.filter(data_ID=datos).latest('fecha')
    except soli.DoesNotExist:
        return HttpResponse("No hay solicitud", status=400)

    print(solicitud)
    documentos = SubirDocs.objects.filter(fuuid__uuid=uuid).order_by('-nomDoc')


    asunto = request.session.get('asunto', 'Sin asunto')
    puo = request.session.get('puo', 'Sin PUO')
    print(puo)
    print(asunto)

    if solicitud and solicitud.folio:
        puo_txt, folio = gen_folio(uid, solicitud.puo), solicitud.folio

        puo_txt = puo_txt[0]
        folio = solicitud.folio
    else:
        puo_txt, folio = gen_folio(uid, solicitud.puo if solicitud else 'general')

    match asunto:
        case "DOP00001":
            asunto = "Arreglo de calles de terracería - DOP00001"
        case "DOP00002":
            asunto = "Bacheo de calles - DOP00002"
        case "DOP00003":
            asunto = "Limpieza de arroyos al sur de la ciudad - DOP00003"
        case "DOP00004":
            asunto = "Limpieza o mantenimiento de rejillas pluviales - DOP00004"
        case "DOP00005":
            asunto = "Pago de costo de participación en licitaciones de obra pública - DOP00005"
        case "DOP00006":
            asunto = "Rehabilitación de calles - DOP00006"
        case "DOP00007":
            asunto = "Retiro de escombro y material de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche/fresado - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de pintura para señalamientos viales - DOP00011"
        case "DOP00012":
            asunto = "Arreglo de derrumbe de bardas - DOP00012"
        case "DOP00013":
            asunto = "Tapiado - DOP00013"

    context = {
        "asunto": asunto,
        "datos": {
            "nombre": datos.nombre,
            "pApe": datos.pApe,
            "mApe": datos.mApe,
            "bDay": datos.bDay,
            "tel": datos.tel,
            "curp": datos.curp,
            "sexo": datos.sexo,
            "dir": datos.dirr,
            "disc": datos.disc,
            "etnia": datos.etnia,
            "vul": datos.vul if datos.vul else "No pertenece a un grupo vulnerable",
        },
        "soli": {
            "dir": solicitud.dirr if solicitud else "",
            "info": solicitud.info,
            "desc": solicitud.descc if solicitud else "",
            "foto": solicitud.foto,
            "fecha": solicitud.fecha,
        },
        'puo': puo_txt,
        'documentos': documentos,
        'folio': folio,
    }
    html = render_to_string("documet/document.html", context)
    buffer = BytesIO()
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(buffer)
    pdf_file = ContentFile(buffer.getvalue())
    nomDoc = f'VS_{asunto}_{datos.nombre}_{datos.pApe}.pdf'
    doc = Files(nomDoc=nomDoc, fuuid=uid, soli_FK=solicitud)
    doc.finalDoc.save(nomDoc, pdf_file)

    return render(request, 'documet/save.html', {'doc':doc})

@login_required
@desur_access_required
def pp_document(request):
    """
    Generar y guardar documento PDF de propuesta de Presupuesto Participativo

    Args:
        request: HttpRequest con UUID en cookies

    Returns:
        HttpResponse con confirmación de documento guardado

    Categories (Presupuesto Participativo):
        - parque: Mejoras en parques (canchas, alumbrado, juegos, etc.)
        - escuela: Mejoras en escuelas (rehabilitación, construcción, canchas)
        - cs: Centro comunitario o salón de usos múltiples
        - infraestructura: Obra vial (bardas, banquetas, pavimentación, señalamiento)
        - pluviales: Soluciones para manejo de agua pluvial

    Context por Categoría:
        Cada categoría tiene campos específicos según su propuesta:
        - cat: Nombre de la categoría
        - datos: Información del promovente y proyecto
        - propuesta: Diccionario con campos específicos de la categoría
        - notas: Notas adicionales específicas
        - folio: Folio generado con formato DOP-CPP
        - instalaciones_dict: Catálogo de tipos de instalaciones
        - estados_dict: Catálogo de estados del proyecto

    Folio Format:
        DOP-CPP-{id:05d}-{uuid[:4]}/{año}

    Side Effects:
        - Genera PDF y lo guarda en PpFiles
        - Asocia documento con PpGeneral y UUID de sesión

    Template:
        documet/pp_document.html (para renderizar PDF)
        documet/save.html (confirmación)
    """
    # SÍ login_required - empleados gestionan documentos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    uuid_object = get_object_or_404(Uuid, uuid=uuid)
    gen_data = get_object_or_404(PpGeneral, fuuid__uuid=uuid)
    cat = request.session.get('categoria', 'sin categoria')
    propuesta = None
    num_folio = gen_pp_folio(gen_data.fuuid)
    context = {}
    instalaciones_dict = dict(PpGeneral.INSTALATION_CHOICES)
    estados_dict = dict(PpGeneral.CHOICES_STATE)

    match cat:
        case "parque":
            cat = "Parques"
            propuesta = PpParque.objects.filter(fk_pp=gen_data).last()

            propuesta_data = {}
            if propuesta:
                propuesta_data = {
                    'cancha_futbol_rapido': propuesta.cancha_futbol_rapido,
                    'cancha_futbol_soccer': propuesta.cancha_futbol_soccer,
                    'cancha_futbol_7x7': propuesta.cancha_futbol_7x7,
                    'cancha_beisbol': propuesta.cancha_beisbol,
                    'cancha_softbol': propuesta.cancha_softbol,
                    'cancha_usos_multiples': propuesta.cancha_usos_multiples,
                    'cancha_otro': propuesta.cancha_otro,
                    'alumbrado_rehabilitacion': propuesta.alumbrado_rehabilitacion,
                    'alumbrado_nuevo': propuesta.alumbrado_nuevo,
                    'juegos_dog_park': propuesta.juegos_dog_park,
                    'juegos_infantiles': propuesta.juegos_infantiles,
                    'juegos_ejercitadores': propuesta.juegos_ejercitadores,
                    'juegos_otros': propuesta.juegos_otro,
                    'techumbre_domo': propuesta.techumbre_domo,
                    'techumbre_kiosko': propuesta.techumbre_kiosko,
                    'equipamiento_botes': propuesta.equipamiento_botes,
                    'equipamiento_bancas': propuesta.equipamiento_bancas,
                    'equipamiento_andadores': propuesta.equipamiento_andadores,
                    'equipamiento_rampas': propuesta.equipamiento_rampas,
                }

            context = {
                "cat":cat,
                "datos":{
                    "nombre": gen_data.nombre_promovente,
                    "telefono": gen_data.telefono,
                    "direccion": gen_data.direccion_proyecto,
                    "desc": gen_data.desc_p,
                    "fecha": gen_data.fecha_pp,
                    "notas": gen_data.notas_importantes,
                    "instalaciones": gen_data.instalation_choices
                },
                "propuesta": propuesta_data,
                "notas_parque": propuesta.notas_parque,
                "folio": num_folio,
                "instalaciones_dict": instalaciones_dict,
                "estados_dict": estados_dict,
            }

        case "escuela":
            cat = "Escuelas"
            propuesta = PpEscuela.objects.filter(fk_pp=gen_data).last()

            propuesta_data = {}
            if propuesta:
                propuesta_data = {
                    'rehabilitacion_baños': propuesta.rehabilitacion_baños,
                    'rehabilitacion_salones': propuesta.rehabilitacion_salones,
                    'rehabilitacion_electricidad': propuesta.rehabilitacion_electricidad,
                    'rehabilitacion_gimnasio': propuesta.rehabilitacion_gimnasio,
                    'rehabilitacion_otro': propuesta.rehabilitacion_otro,
                    'construccion_domo': propuesta.construccion_domo,
                    'construccion_aula': propuesta.construccion_aula,
                    'cancha_futbol_rapido': propuesta.cancha_futbol_rapido,
                    'cancha_usos_multiples': propuesta.cancha_usos_multiples,
                    'cancha_futbol_7x7': propuesta.cancha_futbol_7x7,
                }

            context = {
                "cat": cat,
                "datos": {
                    "nombre": gen_data.nombre_promovente,
                    "telefono": gen_data.telefono,
                    "direccion": gen_data.direccion_proyecto,
                    "desc": gen_data.desc_p,
                    "fecha": gen_data.fecha_pp,
                    "instalaciones": gen_data.instalation_choices,
                    "notas": gen_data.notas_importantes,
                },
                "nom_escuela": propuesta.nom_escuela,
                "propuesta": propuesta_data,
                "notas": propuesta.notas_escuela,
                "folio": num_folio,
                "instalaciones_dict": instalaciones_dict,
                "estados_dict": estados_dict,
            }

        case "cs":
            cat = "Centro comunitario - Salón de usos múltiples"
            propuesta = PpCS.objects.filter(fk_pp=gen_data).last()

            propuesta_data = {}
            if propuesta:
                propuesta_data = {
                    'rehabilitacion_baños': propuesta.rehabilitacion_baños,
                    'rehabilitacion_salones': propuesta.rehabilitacion_salones,
                    'rehabilitacion_electricidad': propuesta.rehabilitacion_electricidad,
                    'rehabilitacion_gimnasio': propuesta.rehabilitacion_gimnasio,
                    'construccion_domo': propuesta.construccion_domo,
                    'construccion_salon': propuesta.construccion_salon,
                    'construccion_otro': propuesta.construccion_otro,
                }

            context = {
                "cat": cat,
                "datos": {
                    "nombre": gen_data.nombre_promovente,
                    "telefono": gen_data.telefono,
                    "direccion": gen_data.direccion_proyecto,
                    "desc": gen_data.desc_p,
                    "fecha": gen_data.fecha_pp,
                    "instalaciones": gen_data.instalation_choices,
                    "notas": gen_data.notas_importantes,
                },
                "notas": propuesta.notas_propuesta,
                "propuesta": propuesta_data,
                "folio": num_folio,
                "instalaciones_dict": instalaciones_dict,
                "estados_dict": estados_dict,
            }
        case "infraestructura":
            cat = "Infraestructura"
            propuesta = PpInfraestructura.objects.filter(fk_pp=gen_data).last()

            propuesta_data = {}
            if propuesta:
                propuesta_data = {
                    'infraestructura_barda': propuesta.infraestructura_barda,
                    'infraestructura_baquetas': propuesta.infraestructura_banquetas,
                    'infraestructura_muro': propuesta.infraestructura_muro,
                    'infraestructura_camellon': propuesta.infraestructura_camellon,
                    'infraestructura_crucero': propuesta.infraestructura_crucero,
                    'infraestructura_ordenamiento': propuesta.infraestructura_ordenamiento,
                    'infraestructura_er': propuesta.infraestructura_er,
                    'infraestructura_mejora': propuesta.infraestructura_mejora,
                    'infraestructura_peatonal': propuesta.infraestructura_peatonal,
                    'infraestructura_bayoneta': propuesta.infraestructura_bayoneta,
                    'infraestructura_topes': propuesta.infraestructura_topes,
                    'infraestructura_puente': propuesta.infraestructura_puente,
                    'pavimentacion_asfalto': propuesta.pavimentacion_asfalto,
                    'paviementacion_rehabilitacion': propuesta.pavimentacion_rehabilitacion,
                    'señalamiento_pintura': propuesta.señalamiento_pintura,
                    'señalamiento_señales': propuesta.señalamiento_señales,
                }

            context = {
                "cat": cat,
                "datos": {
                    "nombre": gen_data.nombre_promovente,
                    "telefono": gen_data.telefono,
                    "direccion": gen_data.direccion_proyecto,
                    "desc": gen_data.desc_p,
                    "fecha": gen_data.fecha_pp,
                    "instalaciones": gen_data.instalation_choices,
                    "notas": gen_data.notas_importantes,
                },
                "notas": propuesta.notas_propuesta,
                "propuesta": propuesta_data,
                "folio": num_folio,
                "instalaciones_dict": instalaciones_dict,
                "estados_dict": estados_dict,
            }

        case "pluviales":
            cat = "Soluciones pluviales"
            propuesta = PpPluvial.objects.filter(fk_pp=gen_data).last()

            propuesta_data = {}
            if propuesta:
                propuesta_data = {
                    'pluvial_muro_contencion': propuesta.pluvial_muro_contencion,
                    'pluvial_canalizacion': propuesta.pluvial_canalizacion,
                    'pluvial_puente_peatonal': propuesta.pluvial_puente_peatonal,
                    'pluvial_vado': propuesta.pluvial_vado,
                    'pluvial_puente': propuesta.pluvial_puente,
                    'pluvial_desalojo': propuesta.pluvial_desalojo,
                    'pluvial_rejillas': propuesta.pluvial_rejillas,
                    'pluvial_lavaderos': propuesta.pluvial_lavaderos,
                    'pluvial_obra_hidraulica': propuesta.pluvial_obra_hidraulica,
                    'pluvial_reposicion_piso': propuesta.pluvial_reposicion_piso,
                    'pluvial_proteccion_inundaciones': propuesta.pluvial_proteccion_inundaciones,
                }

            context = {
                "cat": cat,
                "datos": {
                    "nombre": gen_data.nombre_promovente,
                    "telefono": gen_data.telefono,
                    "direccion": gen_data.direccion_proyecto,
                    "desc": gen_data.desc_p,
                    "fecha": gen_data.fecha_pp,
                    "instalaciones": gen_data.instalation_choices,
                    "notas": gen_data.notas_importantes,
                },
                "propuesta": propuesta_data,
                "notas": propuesta.notas_propuesta,
                "folio": num_folio,
                "instalaciones_dict": instalaciones_dict,
                "estados_dict": estados_dict,
            }



    #html = render_to_string("documet/pp_document.html", context)
    #pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/'))
    #final_pdf = pdf_out.write_pdf()
    #response = HttpResponse(final_pdf, content_type="application/pdf")
    #response["Content-Disposition"] = "inline; filename=información_general.pdf"
    #return response

    html = render_to_string("documet/pp_document.html", context)
    buffer = BytesIO()
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(buffer)
    pdf_file = ContentFile(buffer.getvalue())
    nomDoc = f'VS_{cat}_{gen_data.nombre_promovente}_Presupuesto_Participativo.pdf'
    doc = Files(nomDoc=nomDoc, fuuid=uuid_object, pp_FK=gen_data)
    doc.finalDoc.save(nomDoc, pdf_file)

    return render(request, 'documet/save.html', {"doc":doc})

@login_required
@desur_access_required
def document2(request):
    """
    Generar documento PDF específico para pagos de licitaciones (DOP00005)

    Args:
        request: HttpRequest con UUID en cookies

    Returns:
        HttpResponse con PDF generado (inline)

    Context:
        - asunto: Descripción del trámite de pago
        - datos: Información personal del ciudadano
        - pago: Información del pago (fecha, forma de pago)

    PDF Format:
        Comprobante de pago para participación en licitación

    Template:
        documet/document2.html
    """
    # SÍ login_required - empleados generan documentos de pago
    uuid = request.COOKIES.get('uuid')
    datos = get_object_or_404(data, fuuid__uuid=uuid)
    pago = get_object_or_404(Pagos, data_ID=datos)

    asunto = request.session.get('asunto', 'Sin asunto')

    if asunto == "DOP00005":
        asunto = "Pago de costo de participación en licitaciones de obra pública - DOP00005"

    context={
        "asunto":asunto,
        "datos":{
            "nombre": datos.nombre,
            "pApe": datos.pApe,
            "mApe": datos.mApe,
            "bDay": datos.bDay,
            "tel": datos.tel,
            "curp": datos.curp,
            "sexo": datos.sexo,
            "dirr": datos.dirr,
        },
        "pago":{
            "fecha":pago.fecha,
            "pfm" : pago.pfm
        },
    }
    html = render_to_string("documet/document2.html", context)
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/'))
    final_pdf = pdf_out.write_pdf()
    response = HttpResponse(final_pdf, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=información_general.pdf"

    return response
    #return render(request, "documet/document2.html")

@login_required
@desur_access_required
def clear(request):
    """
    Limpiar sesión de trabajo eliminando cookie UUID y redirigiendo al menú

    Args:
        request: HttpRequest

    Returns:
        HttpResponse redirect con cookie UUID eliminada

    Side Effects:
        - Elimina cookie 'uuid' del navegador
        - No elimina datos de BD, solo termina la sesión de trabajo

    Use Case:
        Se llama al finalizar un trámite para limpiar estado temporal
    """
    response = redirect('home')  # Cambiar redirect a login de empleados
    response.delete_cookie('uuid')
    return response


# ============================================================================
# FUNCIONES AUXILIARES Y UTILIDADES
# ============================================================================

def gen_folio(uid, puo):
    """
    Genera folio único para trámites con formato estandarizado y validaciones

    Args:
        uid: UUID object o string con el UUID de sesión
        puo: Código del tipo de proceso (OFI, CRC, MEC, DLO, etc.)

    Returns:
        tuple: (puo_txt, folio)
            - puo_txt: Descripción legible del tipo de proceso
            - folio: Folio generado con formato DOP-{PUO}-{id:05d}-{uuid[:4]}/{año}

    Folio Format:
        DOP-{PUO}-{id:05d}-{uuid_prefix}/{year}
        - DOP: Gobierno de Obra Pública
        - PUO: Código del proceso (3 letras)
        - id: ID numérico con padding de 5 dígitos
        - uuid_prefix: Primeros 4 caracteres del UUID
        - year: Últimos 2 dígitos del año actual

    Procesos Válidos (PUO):
        - OFI: Oficio
        - CRC: CRC (Comité de Recursos Ciudadanos)
        - MEC: Marca el cambio
        - DLO: Diputado Local
        - DFE: Diputado Federal
        - REG: Regidores
        - DEA: Despacho del Alcalde
        - EVA: Evento con el Alcalde
        - PED: Presencial en Dirección
        - VIN: Vinculación (default si PUO no reconocido)
        - PPA: Presupuesto participativo
        - CPC: Coordinación de Participación Ciudadana

    Error Handling:
        Si ocurre error, retorna ('Error', 'ERROR-{uuid[:8]}')
    """
    logger.debug("Generando folio para trámite")
    uid_str = ""

    try:
        if isinstance(uid, str):
            uuid_obj = Uuid.objects.get(uuid=uid)
        elif isinstance(uid, Uuid):
            uuid_obj = uid
        else:
            raise ValueError(f"UUID inválido {type(uid)}")


        uuid_id = uuid_obj.prime
        uid_str = str(uuid_obj.uuid)

        fecha = date.today()
        year_str = str(fecha.year)
        year_slice = year_str[2:4]

        match puo:
            case 'OFI':
                folio = f'DOP-OFI-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Oficio'
            case 'CRC':
                folio = f'DOP-CRC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'CRC'
            case 'MEC':
                folio = f'DOP-MEC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Marca el cambio'
            case 'DLO':
                folio = f'DOP-DLO-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Diputado Local'
            case 'DFE':
                folio = f'DOP-DFE-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Diputado Federal'
            case 'REG':
                folio = f'DOP-REG-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Regidores'
            case 'DEA':
                folio = f'DOP-DEA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Despacho del Alcalde'
            case 'EVA':
                folio = f'DOP-EVA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Evento con el Alcalde'
            case 'PED':
                folio = f'DOP-PED-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Presencial en Dirección'
            case 'VIN':
                folio = f'DOP-VIN-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Vinculación'
            case 'PPA':
                folio = f'DOP-PPA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Presupuesto participativo'
            case 'CPC':
                folio = f'DOP-CPC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Coordinación de Participación Ciudadana'
            case _:
                folio = f'DOP-VIN-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'General'

        logger.info(f"Folio generado correctamente: {folio}")
        return puo_txt, folio

    except Exception as e:
        logger.error(f"Error generando folio: {str(e)}")
        return 'Error', f'ERROR-{uid_str[:8]}'

def gen_pp_folio(fuuid):
    """
    Genera folio específico para propuestas de Presupuesto Participativo

    Args:
        fuuid: Objeto Uuid de la sesión

    Returns:
        str: Folio con formato DOP-CPP-{id:05d}-{uuid[:4]}/{año}

    Folio Format:
        DOP-CPP-{id:05d}-{uuid_prefix}/{year}
        - CPP: Código fijo para Presupuesto Participativo
        - id: ID del registro PpGeneral con padding de 5 dígitos
        - uuid_prefix: Primeros 4 caracteres del UUID
        - year: Últimos 2 dígitos del año actual

    Error Handling:
        Si ocurre error, retorna 'ERROR-PP-{uuid[:8]}'
    """
    try:
        pp_info = PpGeneral.objects.filter(fuuid=fuuid).last()
        uid_str = str(fuuid.uuid)
        id_pp = pp_info.pk if pp_info else 0 # Valor por defecto

        fecha = date.today()
        year_str = str(fecha.year)
        year_slice = year_str[2:4]

        folio = f'DOP-CPP-{id_pp:05d}-{uid_str[:4]}/{year_slice}'

        logger.debug("Folio de PP generado correctamente")
        return folio

    except Exception as e:
        logger.error(f"Error generando folio PP: {str(e)}")
        return f'ERROR-PP-{str(fuuid.uuid)[:8]}'

def validar_curp(curp):
    """
    Valida formato de CURP según estándar mexicano oficial

    Args:
        curp: String con CURP a validar (debe ser uppercase)

    Returns:
        bool: True si el formato es válido

    Raises:
        ValidationError: Si el formato no cumple con el patrón

    CURP Format:
        - 4 letras (primer apellido, segundo apellido, nombre)
        - 6 dígitos (fecha: AAMMDD)
        - 1 letra (sexo: H/M)
        - 5 letras (lugar de nacimiento + consonantes internas)
        - 1 caracter (verificador numérico o letra A)
        - 1 dígito (verificador final)

    Pattern:
        ^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-1A-Z][0-9]$
    """
    pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-1A-Z][0-9]$'
    if not re.match(pattern, curp):
        logger.warning("CURP con formato incorrecto detectado")
        raise ValidationError("El formato del CURP es incorrecto.")
    return True

def validar_datos(post_data):
    """
    Valida exhaustivamente todos los campos del formulario de datos del ciudadano

    Args:
        post_data: Diccionario con datos del formulario (request.POST)

    Returns:
        list: Lista de errores encontrados (vacía si todo es válido)

    Validaciones por Campo:

        nombre:
            - Obligatorio, min 2 caracteres
            - Solo letras, espacios y acentos

        pApe (apellido paterno):
            - Obligatorio, min 2 caracteres
            - Solo letras, espacios y acentos

        mApe (apellido materno):
            - Obligatorio, min 2 caracteres
            - Solo letras, espacios y acentos

        bDay (fecha de nacimiento):
            - Obligatorio, formato YYYY-MM-DD
            - No puede ser fecha futura
            - Edad válida (0-120 años)

        tel (teléfono):
            - Obligatorio
            - Solo dígitos (se permiten espacios, guiones y paréntesis que se eliminan)
            - 10-15 dígitos

        curp:
            - Obligatorio
            - Formato válido según validar_curp()

        sexo:
            - Obligatorio
            - Valores permitidos: mujer, hombre, M, H, Masculino, Femenino

        dir (dirección):
            - Obligatorio, min 10 caracteres
            - Se valida contra catastro si LocalGISService está disponible

        asunto:
            - Obligatorio

    Side Effects:
        - Registra warnings en log si dirección no se encuentra en catastro
    """
    errors = []

    # Validar nombre
    nombre = post_data.get('nombre', '').strip()
    if not nombre:
        errors.append("El nombre es obligatorio")
    elif len(nombre) < 2:
        errors.append("El nombre debe tener al menos 2 caracteres")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
        errors.append("El nombre solo puede contener letras y espacios")

    # Validar apellido paterno
    pApe = post_data.get('pApe', '').strip()
    if not pApe:
        errors.append("El apellido paterno es obligatorio")
    elif len(pApe) < 2:
        errors.append("El apellido paterno debe tener al menos 2 caracteres")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', pApe):
        errors.append("El apellido paterno solo puede contener letras y espacios")

    # Validar apellido materno
    mApe = post_data.get('mApe', '').strip()
    if not mApe:
        errors.append("El apellido materno es obligatorio")
    elif len(mApe) < 2:
        errors.append("El apellido materno debe tener al menos 2 caracteres")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', mApe):
        errors.append("El apellido materno solo puede contener letras y espacios")

    # Validar fecha de nacimiento
    bDay = post_data.get('bDay', '').strip()
    if not bDay:
        errors.append("La fecha de nacimiento es obligatoria")
    else:
        try:
            from datetime import datetime, date
            fecha_nacimiento = datetime.strptime(bDay, '%Y-%m-%d').date()
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

            if fecha_nacimiento > hoy:
                errors.append("La fecha de nacimiento no puede ser futura")
            elif edad > 120:
                errors.append("La fecha de nacimiento no es válida")
            elif edad < 0:
                errors.append("La fecha de nacimiento no es válida")
        except ValueError:
            errors.append("Formato de fecha de nacimiento inválido")

    # Validar teléfono
    tel = post_data.get('tel', '').strip()
    if not tel:
        errors.append("El teléfono es obligatorio")
    else:
        # Remover espacios, guiones y paréntesis para validación
        tel_limpio = re.sub(r'[\s\-\(\)]', '', tel)
        if not tel_limpio.isdigit():
            errors.append("El teléfono solo puede contener números")
        elif len(tel_limpio) < 10:
            errors.append("El teléfono debe tener al menos 10 dígitos")
        elif len(tel_limpio) > 15:
            errors.append("El teléfono no puede tener más de 15 dígitos")

    # Validar CURP
    curp = post_data.get('curp', '').strip().upper()
    if not curp:
        errors.append("El CURP es obligatorio")
    else:
        try:
            validar_curp(curp)
        except ValidationError as e:
            errors.append(str(e))

    # Validar sexo
    sexo = post_data.get('sexo', '').strip()
    if not sexo:
        errors.append("El sexo es obligatorio")
    elif sexo not in ['M', 'F', 'Masculino', 'Femenino']:
        errors.append("El sexo debe ser M (Masculino) o F (Femenino)")

    # Validar dirección
    direccion = post_data.get('dir', '').strip()
    if not direccion:
        errors.append("La dirección es obligatoria")
    elif len(direccion) < 10:
        errors.append("La dirección debe ser más específica")
    else:
        try:
            if not LocalGISService.validate_address(direccion):
                logger.warning(f"Direccion no encontrada en catastro: {direccion}")
        except Exception as e:
            logger.error(f"Error validando la dirección: {str(e)}")

    # Validar asunto
    asunto = post_data.get('asunto', '').strip()
    if not asunto:
        errors.append("El asunto es obligatorio")

    return errors


def soli_processed(request, uid, dp):
    """
    Procesa y guarda solicitud completa de trámite con documentos adjuntos

    Args:
        request: HttpRequest con datos de solicitud (POST)
        uid: Objeto Uuid de la sesión actual
        dp: Objeto data con información del ciudadano

    Returns:
        JsonResponse o HttpResponse redirect según resultado

    Process Flow:
        1. Valida método POST y datos obligatorios
        2. Procesa dirección del problema
        3. Valida y limpia descripción e información adicional
        4. Valida PUO (tipo de proceso)
        5. Procesa documentos temporales en base64
        6. Procesa imagen principal de la solicitud
        7. Genera folio único
        8. Crea registro en modelo soli
        9. Redirige a generación de documento

    Form Fields:
        - dir: Dirección del problema (obligatorio)
        - descc: Descripción detallada (opcional, default: "Sin descripción proporcionada")
        - info: Información adicional (opcional, default: "Sin información adicional")
        - puo: Tipo de proceso/origen (obligatorio, debe ser válido)
        - src: Imagen del problema (File o base64)
        - temp_docs_count: Cantidad de documentos temporales
        - temp_doc_{i}: Datos JSON en base64 de cada documento temporal

    Valid PUOs:
        OFI, CRC, MEC, DLO, DFE, REG, DEA, EVA, PED, VIN, PPA, CPC

    Document Processing:
        - Decodifica documentos en base64 del POST
        - Elimina prefijo 'data:tipo;base64,' si existe
        - Guarda cada documento en SubirDocs

    Side Effects:
        - Guarda PUO en session
        - Crea registro en soli con folio generado
        - Crea registros en SubirDocs para documentos temporales
        - Asocia solicitud con usuario que la procesó (processed_by)

    Error Handling:
        - Retorna JsonResponse con error 400/405/500 según caso
        - Registra todos los errores en logger
        - Usa transaction.atomic() para rollback en caso de error

    Security:
        - Valida UUID de sesión
        - Requiere autenticación y permisos DesUr
        - Valida formato de datos recibidos
    """
    try:
        with transaction.atomic():
            # Validar que la solicitud venga con método POST
            if request.method != 'POST':
                logger.warning("Intento de acceso a soli_processed sin método POST")
                return JsonResponse({'error': 'Método no permitido'}, status=405)

            # Validar datos de entrada
            dirr = request.POST.get('dir', '').strip()
            if not dirr:
                logger.warning("Solicitud sin dirección")
                return JsonResponse({'error': 'La dirección es obligatoria'}, status=400)

            logger.info(f"Procesando solicitud de trámite para usuario {request.user.username}")

            """
            # Procesar dirección de forma segura
            try:
                calle, colonia, cp = cut_direction(dirr)
            except Exception as e:
                logger.error(f"Error procesando dirección: {str(e)}")
                calle, colonia, cp = dirr, "", ""
            """

            # Validar y limpiar campos opcionales
            descc = request.POST.get('descc', '').strip()
            print(descc)
            if not descc:
                logger.debug("Solicitud sin descripción")
                descc = "Sin descripción proporcionada"

            info = request.POST.get('info', '').strip()
            if not info:
                logger.debug("Solicitud sin información adicional")
                info = "Sin información adicional"

            # Validar PUO
            puo = request.POST.get('puo', '').strip()
            if not puo:
                logger.warning("Solicitud sin PUO especificado")
                return JsonResponse({'error': 'El tipo de proceso (PUO) es obligatorio'}, status=400)

            # Validar que el PUO sea válido
            valid_puos = ['OFI', 'CRC', 'MEC', 'DLO', 'DFE', 'REG', 'DEA', 'EVA', 'PED', 'VIN', 'PPA', 'CPC']
            if puo not in valid_puos:
                logger.warning(f"PUO inválido recibido: {puo}")
                return JsonResponse({'error': 'Tipo de proceso no válido'}, status=400)

            request.session['puo'] = puo

            # Procesar imagen con validación mejorada
            img = img_processed(request)
            if not img:
                logger.warning("No se pudo procesar la imagen de la solicitud")
                #return JsonResponse({'error': 'No se pudo procesar la imagen. Verifique el formato.'}, status=400)

            # En la función soli_processed, corregir estas líneas:

        temp_docs_count = request.POST.get('temp_docs_count', '0')
        if temp_docs_count.isdigit():
            count = int(temp_docs_count)
            logger.info(f"Procesando {count} documentos temporales")

            # ✅ Obtener el objeto Uuid correctamente según el tipo de uid
            if isinstance(uid, str):
                uuid_obj = get_object_or_404(Uuid, uuid=uid)
            else:
                # uid ya es un objeto Uuid
                uuid_obj = uid

            for i in range(count):
                temp_doc_data = request.POST.get(f'temp_doc_{i}')
                if temp_doc_data:
                    print(f"Documento {i}: {temp_doc_data[:100]}")
                    try:
                        doc_info = json.loads(temp_doc_data)
                        file_data = doc_info['fileData']

                        # Remover el prefijo data:tipo;base64, si existe
                        if ',' in file_data:
                            file_data = file_data.split(',')[1]

                        file_content = base64.b64decode(file_data)
                        file_name = doc_info['name']
                        file_desc = doc_info['desc']

                        # Crear archivo Django
                        django_file = ContentFile(file_content, name=file_name)

                        # Guardar en la base de datos con el objeto correcto
                        nuevo_doc = SubirDocs(
                            nomDoc=file_name,
                            descDoc=file_desc,
                            fuuid=uuid_obj,  # ✅ Usar el objeto Uuid correcto
                            doc=django_file  # ✅ Verificar que el campo sea 'doc' no 'ffile'
                        )
                        nuevo_doc.save()
                        logger.info(f"Documento temporal guardado: {file_name}")

                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.error(f"Error procesando documento temporal {i}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error guardando documento temporal {i}: {str(e)}")
                        continue

        # Procesar imagen
        img = img_processed(request)

        # ✅ Generar folio con el objeto correcto
        if isinstance(uid, str):
            uuid_obj_folio = get_object_or_404(Uuid, uuid=uid)
        else:
            uuid_obj_folio = uid

        puo_txt, folio = gen_folio(uuid_obj_folio, puo)

        # Crear la solicitud
        nueva_solicitud = soli(
            dirr=dirr,
            info=info,
            descc=descc,
            foto=img,
            data_ID=dp,
            puo=puo,
            processed_by=request.user,
            folio=folio
        )
        nueva_solicitud.save()

        logger.info(f"Solicitud procesada exitosamente: {folio}")
        messages.success(request, "Solicitud procesada exitosamente")
        return redirect('doc')

    except Exception as e:
        logger.error(f"Error crítico procesando solicitud: {str(e)}")
        import traceback

        traceback.print_exc()
        messages.error(request, "Error al procesar la solicitud")
        return redirect('soli')


def img_processed(request):
    """
    Procesa imagen de solicitud desde archivo o base64 con validaciones

    Args:
        request: HttpRequest con imagen en FILES['src'] o POST['src']

    Returns:
        ContentFile: Objeto File de Django con imagen procesada
        None: Si no hay imagen o hay error en procesamiento

    Input Formats:
        1. File Upload: request.FILES['src']
        2. Base64: request.POST['src'] con formato 'data:image/...;base64,{data}'

    Process (Base64):
        1. Separa header y datos codificados
        2. Decodifica base64 a bytes
        3. Guarda temporalmente en archivo
        4. Lee archivo y crea ContentFile
        5. Elimina archivo temporal

    File Naming:
        - Extrae nombre original del archivo
        - Asegura extensión .jpg
        - Format: {nombre}.jpg

    Error Handling:
        - Retorna None si hay error
        - Registra error en logger

    Side Effects:
        - Crea y elimina archivo temporal si procesa base64
    """
    img = None
    imgpath = request.POST.get('src')

    if 'src' in request.FILES:
        img = request.FILES['src']
    elif imgpath and imgpath.startswith("data:image"):
        try:
            header, encoded = imgpath.split(",", 1)
            datos = base64.b64decode(encoded)

            import tempfile
            import os

            tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            tmp_img.write(datos)
            tmp_img.flush()
            tmp_img.close()

            with open(tmp_img.name, 'rb') as f:
                content = f.read()

            os.unlink(tmp_img.name)

            img = ContentFile(content, name='uploaded_image.jpg')
        except Exception as e:
            logger.error(f"Error procesando imagen base64: {str(e)}")
            return None
    else:
        logger.warning("No se encontró imagen para procesar")
        return None

    if img and hasattr(img, 'name'):
        name = str(img.name).split("\\")[-1]
        if not name.endswith('.jpg'):
            name += '.jpg'
        img.name = name

    return img

def files_processed(request, uid):
    """
    Procesa múltiples archivos adjuntos subidos en formulario

    Args:
        request: HttpRequest con archivos en FILES
        uid: Objeto Uuid de la sesión

    Returns:
        None (procesa archivos como side effect)

    File Fields:
        Busca campos con patrón: 'tempfile_{index}'

    Description Fields:
        Busca descripción en múltiples formatos:
        - tempdesc_{index}
        - desc {index}
        - descripcion_{index}
        - desc
        - description

    Fallback Description:
        Si no hay descripción, usa nombre del archivo sin extensión

    Duplicate Handling:
        No guarda archivos duplicados (mismo nombre y UUID)

    Side Effects:
        - Crea registros en SubirDocs para cada archivo
        - Guarda archivos físicos en media/documents/

    Error Handling:
        - Registra errores en logger pero continúa con siguientes archivos
        - No interrumpe el proceso si un archivo falla
    """
    file_keys = [k for k in request.FILES.keys() if k.startswith('tempfile_')]

    if file_keys:
        for key in file_keys:
            try:
                index = key.split('_')[-1]
                file = request.FILES[key]
                desc_field_names = [
                    f'tempdesc_{index}',
                    f'desc {index}',
                    f'descripcion_{index}',
                    'desc',
                    'description'
                ]

                desc = 'Documento sin descripcion'

                for desc_field in desc_field_names:
                    if desc_field in request.POST:
                        desc = request.POST.get(desc_field, '').strip()
                        if desc:
                            break

                if desc == 'Documento sin descripcion':
                    file_name =getattr(file, 'name', '')
                    if file_name:
                        desc = file_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

                if not SubirDocs.objects.filter(fuuid=uid, nomDoc=file.name).exists():
                    logger.debug(f"Guardando nuevo documento: {file.name}")
                    documento = SubirDocs(
                        descDoc=desc,
                        doc=file,
                        nomDoc=file.name,
                        fuuid=uid,
                    )
                    documento.save()
                else:
                    logger.warning("Documento duplicado, no se guardará")
            except Exception as e:
                logger.error(f"Error procesando archivo {key}: {str(e)}")

def user_errors(request, error):
    """
    Maneja y muestra errores del sistema de forma amigable para el usuario

    Args:
        request: HttpRequest actual
        error: Exception o mensaje de error

    Returns:
        HttpResponse con página de error personalizada

    Context:
        - error: Diccionario con información del error
            - titulo: Título del error
            - mensaje: Mensaje amigable para el usuario
            - codigo: Código del error (SYS_ERROR)
            - accion: Acción sugerida para el usuario

    Side Effects:
        - Registra el error completo con stack trace en logger

    Template:
        error.html
    """
    logger.error(f"Error en vista: {error}", exc_info=True)

    return render(request, 'error.html', {
        'error': {
            'titulo': "Error del sistema",
            'mensaje': 'Por favor, inténtelo nuevamente o contacte al administrador',
            'codigo': 'SYS_ERROR',
            'accion': 'Reintentar'
        }
    })

def validate_file_size(file):
    """
    Valida que el tamaño del archivo no supere el límite permitido (5 MB)

    Args:
        file: Archivo a validar (objeto File de Django)

    Raises:
        ValidationError: Si el archivo es mayor a 5 MB
    """
    limite = 5 * 1024 * 1024
    if file.size > limite:
        raise ValidationError('El archivo no puede ser mayor a 5 MB')

@csrf_exempt
@require_http_methods(["POST"])
def geocode_view(request):
    """Vista optimizada para geocodificación rápida"""
    start_time = timezone.now()

    try:
        data = json.loads(request.body)
        address = data.get('address', '').strip()

        if not address:
            return JsonResponse({
                'success': False,
                'error': 'Dirección vacía'
            })

        if len(address) < 2:
            return JsonResponse({
                'success': False,
                'error': 'Dirección muy corta'
            })

        logger.info(f" Geocodificando: {address}")

        # Intentar geocodificación con timeout general
        try:
            result = LocalGISService.geocode_address(address)

            processing_time = (timezone.now() - start_time).total_seconds()

            if result:
                logger.info(f" Encontrado en {processing_time:.2f}s: {result['address']}")
                return JsonResponse({
                    'success': True,
                    'result': result,
                    'processing_time': processing_time
                })
            else:
                logger.warning(f" No encontrado en {processing_time:.2f}s: {address}")
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontró la dirección',
                    'suggestions': LocalGISService._get_suggestions(address),
                    'processing_time': processing_time
                })

        except Exception as geo_error:
            processing_time = (timezone.now() - start_time).total_seconds()
            logger.error(f"Error geocodificación en {processing_time:.2f}s: {str(geo_error)}")

            return JsonResponse({
                'success': False,
                'error': 'Error en el servicio de geocodificación',
                'processing_time': processing_time
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        processing_time = (timezone.now() - start_time).total_seconds()
        logger.error(f"Error general en geocodificación: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'processing_time': processing_time
        })

@staticmethod
def _get_suggestions(address):
    """Proporciona sugerencias para direcciones no encontradas"""
    suggestions = []

    # Sugerencias basadas en la entrada
    if any(word in address.lower() for word in ['casa', 'num', '#']):
        suggestions.append("Intenta: 'Calle [nombre] [número], Chihuahua'")

    if 'burkina faso' in address.lower():
        suggestions.extend([
            "Calle Burkina Faso 1721, Chihuahua",
            "1721 Burkina Faso, Bosques del Pedregal",
            "Burkina Faso, CP 31203"
        ])

    return suggestions[:3]  # Máximo 3 sugerencias

@csrf_exempt
@require_http_methods(["POST"])
def reverse_geocode_view(request):
    """Vista para geocodificación inversa (coordenadas → dirección)"""
    start_time = timezone.now()

    try:
        data = json.loads(request.body)
        lat = data.get('lat')
        lng = data.get('lng')

        if lat is None or lng is None:
            return JsonResponse({
                'success': False,
                'error': 'Coordenadas lat/lng son requeridas'
            })

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Coordenadas deben ser números válidos'
            })

        # Validar rango de coordenadas para Chihuahua
        if not (-107.5 <= lng <= -105.0 and 27.0 <= lat <= 30.0):
            return JsonResponse({
                'success': False,
                'error': 'Coordenadas fuera del área de cobertura (Chihuahua)'
            })

        logger.info(f" Geocodificación inversa: {lat}, {lng}")

        try:
            result = LocalGISService.reverse_geocode(lat, lng)
            processing_time = (timezone.now() - start_time).total_seconds()

            if result:
                logger.info(f" Geocodificación inversa exitosa en {processing_time:.2f}s: {result.get('address', 'Sin dirección')}")
                return JsonResponse({
                    'success': True,
                    'result': result,
                    'processing_time': processing_time
                })
            else:
                logger.warning(f" No se encontró dirección para {lat}, {lng} en {processing_time:.2f}s")
                return JsonResponse({
                    'success': False,
                    'error': f'No se encontró dirección para las coordenadas {lat:.6f}, {lng:.6f}',
                    'processing_time': processing_time
                })

        except Exception as geo_error:
            processing_time = (timezone.now() - start_time).total_seconds()
            logger.error(f"Error en geocodificación inversa: {str(geo_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Error en el servicio de geocodificación: {str(geo_error)}',
                'processing_time': processing_time
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        processing_time = (timezone.now() - start_time).total_seconds()
        logger.error(f"Error general en geocodificación inversa: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'processing_time': processing_time
        })

# Implementación de WsDomicilios
def get_wsd_client():
    config = WSDConfig()

    return WsDomicilios(
        base_url=config.BASE_URL,
        windows_user=config.WINDOWS_USER,
        windows_password=config.WINDOWS_PASSWORD
    )

def consulta_colonias(request):
    """
    Consulta de colonias desde el servicio web municipal
    """
    try:
        client = get_wsd_client()

        if not client.get_token(client.windows_user, client.windows_password):
            messages.error(request, "No se pudo conectar al servicio de domicilios.")
            return redirect('home')

        colonias = client.get_colonias()
        if not colonias:
            messages.warning(request, "No se encontraron colonias")
            colonias = []

        context = {
            'colonias': colonias,
            'total': len(colonias),
        }

        return render(request, 'modals/direcciones.html', context)

    except Exception as e:
        logger.error(f"Error consultado colonias: {str(e)}")
        messages.error(request, f"Error consultando colonias: {str(e)}")
        return redirect('home')

@csrf_exempt
@require_http_methods(["POST"])
def get_calles(request):
    """Ajax mejorado para búsqueda de colonias, calles y números"""
    try:
        #body = json.loads(request.body)
        data = json.loads(request.body)

        client = get_wsd_client()
        if not client.get_token(client.windows_user, client.windows_password):
            return JsonResponse({
                'success': False,
                'error': 'No se pudo conectar al servicio'
            })

        # Búsqueda de colonias
        if 'search_colonia' in data:
            query = data['search_colonia']
            colonias = client.search_colonia(query)

            logger.debug(f"query: {query}")
            logger.debug(f"Colonias: {len(colonias) if colonias else 0}")
            logger.debug(f"Datos: {colonias}")

            colonias_formateadas = [{
                'id': c.get('id_colonia'),
                'nombre': c.get('colonia', ''),
                'codigo_postal': c.get('cp', '')
            } for c in colonias]

            return JsonResponse({
                'success': True,
                'colonias': colonias_formateadas,
                'total': len(colonias) if colonias else 0
            })

        #Búsqueda por CP
        if 'search_cp' in data:
            cp = data['search_cp'].strip()

            if not cp.isdigit() or len(cp) != 5:
                return JsonResponse({
                    'success': False,
                    'error': 'El código postal debe ser un número de 5 dígitos'
                })

            colonias = client.search_colonia_by_cp(cp)

            logger.debug(f"Búsqueda por cp {cp}")
            logger.debug(f"Volonias encontradas: {len(colonias) if colonias else 0}")

            colonias_formateadas = [{
                'id': c.get('id_colonia'),
                'nombre': c.get('colonia', ''),
                'codigo_postal': c.get('cp', '')
            } for c in colonias]

            return JsonResponse({
                'success': True,
                'colonias': colonias_formateadas,
                'total': len(colonias) if colonias else 0
            })

        # Búsqueda de calles
        if 'id_colonia' in data and 'search_calle' in data:
            id_colonia = int(data['id_colonia'])
            query = data['search_calle']
            calles = client.search_calle(id_colonia, query)

            calles_formateadas = [{
                'id': c.get('id_calle'),
                'nombre': c.get('calle', '')
            } for c in calles]

            return JsonResponse({
                'success': True,
                'calles': calles_formateadas,
                'total': len(calles) if calles else 0
            })

        # Obtener números de calle
        if 'id_colonia' in data and 'id_calle' in data:
            id_colonia = int(data['id_colonia'])
            id_calle = int(data['id_calle'])
            numeros = client.get_ext_num(id_colonia, id_calle)

            numeros_formateados = [{
                'numero': n.get('numero', '')
            } for n in numeros]

            return JsonResponse({
                'success': True,
                'numeros': numeros_formateados,
                'total': len(numeros) if numeros else 0
            })

        return JsonResponse({
            'success': False,
            'error': 'Parámetros incompletos'
        })

    except Exception as e:
        logger.error(f"Error en get_calles: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@desur_access_required
def domicilios(request):
    """
      Renderiza modal de búsqueda de direcciones con autocompletado WSD

      Args:
          request: HttpRequest con sesión activa

      Returns:
          HttpResponse con template del modal

      Template:
          modals/buscar_direccion.html
      """
    try:
        client = get_wsd_client()

        if not client.get_token(client.windows_user, client.windows_password):
            messages.error(request, "No se pudo conectar al sercivio")
            return redirect('home')

        nombre_colonia = request.POST.get('colonia', '').strip()
        nombre_calle = request.POST.get('calle', '').strip()
        id_colonia = request.POST.get('id_colonia')
        id_calle = request.POST.get('id_calle')

        resultados = {}

        #Buscar colonias
        if nombre_colonia:
            resultados['colonias'] = client.search_colonia(nombre_colonia)

        # Buscar calles
        if id_colonia and nombre_calle:
            resultados['calles'] = client.search_calle(
                int(id_colonia),
                nombre_calle
            )

        # Obtener números de calle
        if id_colonia and id_calle:
            resultados['numeros'] = client.get_ext_num(
                int(id_colonia),
                int(id_calle)
            )

        context = {
            'resultados': resultados,
            'busqueda': {
                'colonia': nombre_colonia,
                'calle': nombre_calle
            },
        }

        return render(request, 'modals/buscar_dirección.html', context)

    except Exception as e:
        logger.error(f"Error de búsqueda: {str(e)}")
        messages.error(request, f"Error: {str(e)}")

    return render(request, 'modals/buscar_direccion.html')


# Presupuesto participativo

@login_required
@desur_access_required
def gen_render(request):
    """Vista principal para datos generales de presupuesto participativo"""
    # Obtener o crear UUID
    uuid_str = request.COOKIES.get('uuid')
    if not uuid_str:
        uuid_str = str(uuid.uuid4())
        uuid_obj = Uuid.objects.create(uuid=uuid_str)
    else:
        try:
            uuid_obj = Uuid.objects.get(uuid=uuid_str)
        except Uuid.DoesNotExist:
            uuid_obj = Uuid.objects.create(uuid=uuid_str)

    if request.method == 'POST':
        logger.debug("Procesando formulario de presupuesto participativo")

        # Crear una copia mutable del POST data
        post_data = request.POST.copy()
        post_data['fuuid'] = uuid_obj.pk  # Agregar el fuuid al formulario

        form = GeneralRender(post_data)  # Usar el POST data modificado
        categoria = request.POST.get('categoria')
        cat_values = ['parque', 'cs', 'escuela', 'infraestructura', 'pluviales']

        if categoria and categoria in cat_values:
            request.session['categoria'] = categoria
            request.session['pp_uuid'] = uuid_str
            logger.info(f"Categoría de PP guardada: {categoria}")
        else:
            messages.error(request, "Categoría inválida")
            response = render(request, 'pp/datos_generales.html', {'form': form, 'uuid': uuid_str})
            response.set_cookie('uuid', uuid_str, max_age=3600)
            return response

        if form.is_valid():
            logger.info("Formulario de PP válido, guardando datos")
            instance = form.save(commit=False)
            instance.fuuid = uuid_obj  # Asegurar que el fuuid esté asignado
            instance.save()

            # Redireccionar según categoría
            match categoria:
                case 'parque':
                    response = redirect('parques')
                case 'cs':
                    response = redirect('centros')
                case 'escuela':
                    response = redirect('escuelas')
                case 'infraestructura':
                    response = redirect('infraestructura')
                case 'pluviales':
                    response = redirect('pluviales')
                case _:
                    response = redirect('gen_render')

            response.set_cookie('uuid', uuid_str, max_age=3600)
            return response
        else:
            logger.warning(f"Errores en formulario PP: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = GeneralRender(initial={'fuuid': uuid_obj.pk})  # Inicializar con fuuid

    response = render(request, 'pp/datos_generales.html', {'form': form, 'uuid': uuid_str})
    response.set_cookie('uuid', uuid_str, max_age=3600)
    return response

@login_required
@desur_access_required
def escuela_render(request):
    """Vista para propuestas de presupuesto participativo en escuelas"""
    # Obtener UUID de la propuesta general
    pp_uuid = request.session.get('pp_uuid')
    if not pp_uuid:
        messages.error(request, "No se encontró una propuesta general. Debes completar los datos generales primero.")
        return redirect('gen_render')

    try:
        uuid_obj = Uuid.objects.get(uuid=pp_uuid)
        pp_general = PpGeneral.objects.get(fuuid=uuid_obj)
    except (Uuid.DoesNotExist, PpGeneral.DoesNotExist):
        messages.error(request, "Propuesta general no encontrada.")
        return redirect('gen_render')

    if request.method == 'POST':
        form = EscuelaRender(request.POST)
        if form.is_valid():
            # Vincular con la propuesta general
            instance = form.save(commit=False)
            instance.fk_pp = pp_general
            instance.save()
            logger.info("Propuesta de escuela guardada exitosamente")
            messages.success(request, "Propuesta de escuela guardada exitosamente.")
            return redirect('pp_document')
        else:
            logger.warning(f"Errores en formulario de escuela: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = EscuelaRender()

    return render(request, 'pp/escuela.html', {'form': form, 'pp_general': pp_general})

@login_required
@desur_access_required
def parque_render(request):
    """Vista para propuestas de presupuesto participativo en parques"""
    # Obtener UUID de la propuesta general
    pp_uuid = request.session.get('pp_uuid')
    if not pp_uuid:
        messages.error(request, "No se encontró una propuesta general. Debes completar los datos generales primero.")
        return redirect('gen_render')

    try:
        uuid_obj = Uuid.objects.get(uuid=pp_uuid)
        pp_general = PpGeneral.objects.get(fuuid=uuid_obj)
    except (Uuid.DoesNotExist, PpGeneral.DoesNotExist):
        messages.error(request, "Propuesta general no encontrada.")
        return redirect('gen_render')

    if request.method == 'POST':
        form = ParqueRender(request.POST)
        if form.is_valid():
            # Vincular con la propuesta general
            instance = form.save(commit=False)
            instance.fk_pp = pp_general
            instance.save()
            logger.info("Propuesta de parque guardada exitosamente")
            messages.success(request, "Propuesta de parque guardada exitosamente.")
            return redirect('pp_document')
        else:
            logger.warning(f"Errores en formulario de parque: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = ParqueRender()

    return render(request, 'pp/parque.html', {'form': form, 'pp_general': pp_general})

@login_required
@desur_access_required
def cs_render(request):
    """Vista para propuestas de centros comunitarios y salones de usos múltiples"""
    # Obtener UUID de la propuesta general
    pp_uuid = request.session.get('pp_uuid')
    if not pp_uuid:
        messages.error(request, "No se encontró una propuesta general. Debes completar los datos generales primero.")
        return redirect('gen_render')

    try:
        uuid_obj = Uuid.objects.get(uuid=pp_uuid)
        pp_general = PpGeneral.objects.get(fuuid=uuid_obj)
    except (Uuid.DoesNotExist, PpGeneral.DoesNotExist):
        messages.error(request, "Propuesta general no encontrada.")
        return redirect('gen_render')

    if request.method == 'POST':
        form = CsRender(request.POST)
        if form.is_valid():
            # Vincular con la propuesta general
            instance = form.save(commit=False)
            instance.fk_pp = pp_general
            instance.save()
            logger.info("Propuesta de centro/salón guardada exitosamente")
            messages.success(request, "Propuesta de centro/salón guardada exitosamente.")
            return redirect('pp_document')
        else:
            logger.warning(f"Errores en formulario de centro/salón: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = CsRender()

    return render(request, 'pp/centro_salon.html', {'form': form, 'pp_general': pp_general})

@login_required
@desur_access_required
def infraestructura_render(request):
    """Vista para propuestas de infraestructura"""
    # Obtener UUID de la propuesta general
    pp_uuid = request.session.get('pp_uuid')
    if not pp_uuid:
        messages.error(request, "No se encontró una propuesta general. Debes completar los datos generales primero.")
        return redirect('gen_render')

    try:
        uuid_obj = Uuid.objects.get(uuid=pp_uuid)
        pp_general = PpGeneral.objects.get(fuuid=uuid_obj)
    except (Uuid.DoesNotExist, PpGeneral.DoesNotExist):
        messages.error(request, "Propuesta general no encontrada.")
        return redirect('gen_render')

    if request.method == 'POST':
        form = InfraestructuraRender(request.POST)
        if form.is_valid():
            # Vincular con la propuesta general
            instance = form.save(commit=False)
            instance.fk_pp = pp_general
            instance.save()
            logger.info("Propuesta de infraestructura guardada exitosamente")
            messages.success(request, "Propuesta de infraestructura guardada exitosamente.")
            return redirect('pp_document')
        else:
            logger.warning(f"Errores en formulario de infraestructura: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = InfraestructuraRender()

    return render(request, 'pp/infraestructura.html', {'form': form, 'pp_general': pp_general})

@login_required
@desur_access_required
def pluvial_render(request):
    """Vista para propuestas de soluciones pluviales"""
    # Obtener UUID de la propuesta general
    pp_uuid = request.session.get('pp_uuid')
    if not pp_uuid:
        messages.error(request, "No se encontró una propuesta general. Debes completar los datos generales primero.")
        return redirect('gen_render')

    try:
        uuid_obj = Uuid.objects.get(uuid=pp_uuid)
        pp_general = PpGeneral.objects.get(fuuid=uuid_obj)
    except (Uuid.DoesNotExist, PpGeneral.DoesNotExist):
        messages.error(request, "Propuesta general no encontrada.")
        return redirect('gen_render')

    if request.method == 'POST':
        form = PluvialRender(request.POST)
        if form.is_valid():
            # Vincular con la propuesta general
            instance = form.save(commit=False)
            instance.fk_pp = pp_general
            instance.save()
            logger.info("Propuesta pluvial guardada exitosamente")
            messages.success(request, "Propuesta pluvial guardada exitosamente.")
            return redirect('pp_document')
        else:
            logger.warning(f"Errores en formulario pluvial: {form.errors}")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = PluvialRender()

    return render(request, 'pp/pluviales.html', {'form': form, 'pp_general': pp_general})

