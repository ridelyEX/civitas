import base64
import uuid
from io import BytesIO
import re
import json

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.db import models  # Agregar esta importación para # Q
from django.utils import timezone
from django.utils.timezone import now
from django_user_agents.templatetags.user_agents import is_mobile
from .models import SubirDocs, soli, data, Uuid, Pagos, Files, PpGeneral, PpParque, PpInfraestructura, PpEscuela, PpCS, PpPluvial, PpFiles, DesUrLoginDate
from .forms import (DesUrUsersRender, DesUrLogin, DesUrUsersConfig, GeneralRender,
                    ParqueRender, EscuelaRender, CsRender, InfraestructuraRender, PluvialRender)
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date
from .auth import DesUrAuthBackend, desur_login_required
from portaldu.cmin.models import Licitaciones
from django.views.decorators.http import require_http_methods
import logging
from django.views.decorators.csrf import csrf_exempt
from .services import LocalGISService
from django.conf import settings
# Configurar logging
logger = logging.getLogger(__name__)


# Vistas de autenticación
def desur_users_render(request):
    # NO login_required - necesario para que administradores creen cuentas de empleados
    if request.method == 'POST':
        form = DesUrUsersRender(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            form.save()
            logger.info(f"Nuevo usuario DesUr creado: {cleaned_data.get('username', 'N/A')}")
            return redirect('desur_login')
        else:
            logger.warning("Error en formulario de registro DesUr")
    else:
        form = DesUrUsersRender()
    return render(request, 'auth/desur_users.html', {'form':form})


def desur_login_view(request):
    # NO login_required - necesario para que empleados inicien sesión
    form = DesUrLogin(request.POST)

    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']

        backend = DesUrAuthBackend()
        user = backend.authenticate(request, username=usuario, password=contrasena)

        if user is not None:
            logger.info(f"Usuario autenticado exitosamente: {usuario}")
            request.session['desur_user_id'] = user.id
            request.session['desur_user_username'] = user.username
            DesUrLoginDate.create(user)
            return redirect('desur_menu')  # Ir al menú del empleado
        else:
            logger.warning(f"Intento de login fallido para usuario: {usuario}")
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, 'auth/desur_login.html', {'form':form})


def desur_logout_view(request):
    # NO login_required - aunque podrías argumentar que sí
    request.session.pop('desur_user_id', None)
    request.session.pop('desur_user_username', None)
    return redirect('desur_login')


@desur_login_required
def desur_user_conf(request):
    # SÍ login_required - solo usuarios autenticados pueden configurar perfil
    usuario = request.user
    if request.method == 'POST':
        form = DesUrUsersConfig(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('desur_menu')  # Cambiar a menu en lugar de login
    else:
        form = DesUrUsersConfig(instance=usuario)
    return render(request, 'auth/desur_user_conf.html', {'form': form})


@desur_login_required
def desur_menu(request):
    # SÍ login_required - menú personal
    return render(request, 'auth/desur_menu.html')


@desur_login_required
def desur_historial(request):
    """Vista para mostrar el historial de trámites procesados por el empleado actual"""
    # Obtener todos los trámites procesados por el usuario actual
    tramites = soli.objects.filter(processed_by=request.user).select_related(
        'data_ID', 'processed_by'
    ).order_by('-fecha')

    # Paginación para manejar muchos resultados
    from django.core.paginator import Paginator
    paginator = Paginator(tramites, 10)  # 10 trámites por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas básicas
    total_tramites = tramites.count()
    tramites_hoy = tramites.filter(fecha__date=now().date()).count()

    # Estadísticas por tipo de trámite (PUO)
    from django.db.models import Count
    stats_by_puo = tramites.values('puo').annotate(
        count=Count('soli_ID')
    ).order_by('-count')

    context = {
        'page_obj': page_obj,
        'total_tramites': total_tramites,
        'tramites_hoy': tramites_hoy,
        'stats_by_puo': stats_by_puo,
        'empleado': request.user,
    }

    return render(request, 'auth/desur_historial.html', context)


@desur_login_required
def desur_buscar_tramite(request):
    """Vista para buscar trámites específicos"""
    tramites = None
    query = None

    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET.get('q')
        if query:
            # Buscar en múltiples campos
            tramites = soli.objects.filter(
                processed_by=request.user
            ).filter(
                # Buscar por folio, nombre del ciudadano, CURP, etc.
                models.Q(folio__icontains=query) |
                models.Q(data_ID__nombre__icontains=query) |
                models.Q(data_ID__pApe__icontains=query) |
                models.Q(data_ID__mApe__icontains=query) |
                models.Q(data_ID__curp__icontains=query) |
                models.Q(puo__icontains=query)
            ).select_related('data_ID', 'processed_by').order_by('-fecha')

    context = {
        'tramites': tramites,
        'query': query,
    }

    return render(request, 'auth/desur_buscar.html', context)


# Vistas del sistema de trámites requieren autenticación
# Solo empleados/funcionarios autorizados pueden operar el sistema

@desur_login_required
def base(request):
    # SÍ login_required - solo empleados pueden acceder al sistema
    uuid = request.COOKIES.get('uuid')

    if not uuid:
        return redirect('home')
    return render(request, 'documet/save.html',{'uuid':uuid})

@desur_login_required
def home(request):
    # SÍ login_required - punto de entrada solo para empleados autenticados
    if request.method == 'POST':
        uuidM = request.COOKIES.get('uuid')
        action = request.POST.get('action')

        if not uuidM:
            uuidM = str(uuid.uuid4())
            new = Uuid(uuid=uuidM)
            new.save()
            logger.info("Nuevo UUID creado para sesión")
        else:
            if not Uuid.objects.filter(uuid=uuidM).exists():
                new = Uuid(uuid=uuidM)
                new.save()
                logger.info("UUID recreado para sesión existente")
        if action == 'op':
            response = redirect('data')
        elif action == 'pp':
            response = redirect('general')
        else:
            response = redirect('home')
        response.set_cookie('uuid', uuidM, max_age=3600)
        return response
    return render(request, 'main.html')

@desur_login_required
def intData(request):
    # SÍ login_required - empleados capturan datos de ciudadanos
    direccion = request.GET.get('dir', '')
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

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
                        logger.error("no jala esto")

        except Exception as e:
            logger.error(f"Error al procesar datos: {str(e)}")
            return HttpResponse('Error al procesar los datos. Vuelva a intentarlo.')

    service_status = LocalGISService.get_service_status()

    context = {
        'dir': direccion,
        'asunto': asunto,
        'uuid':uuid,
        'local_gis_enabled': True,
        'gis_services': LocalGISService.SERVICES,
        'service_status': service_status,
    }
    return render(request, 'di.html', context)


@desur_login_required
def soliData(request):
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

        service_status = LocalGISService.get_service_status()

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
            'local_gis_enabled': True,
            'gis_services': LocalGISService.SERVICES,
            'service_status': service_status,
            'fecha': fecha,
        }

        return render(request, 'ds.html', context)
    except Exception as e:
        return user_errors(request, e)

@desur_login_required
def doc(request):
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

@desur_login_required
def dell(request, id):
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

@desur_login_required
def docs(request):
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


@desur_login_required
def docs2(request):
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
    # SÍ, login_required - empleados procesan pagos
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


@desur_login_required
def document(request):
    # SÍ login_required - empleados generan documentos oficiales
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


@desur_login_required
def save_document(request):
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

@desur_login_required
def pp_document(request):
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
    doc = PpFiles(nomDoc=nomDoc, fuuid=uuid_object, fk_pp=gen_data)
    doc.finalDoc.save(nomDoc, pdf_file)

    return render(request, 'documet/save.html', {"doc":doc})



@desur_login_required
def document2(request):
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

@desur_login_required
def clear(request):
    # SÍ login_required - solo empleados limpian sesiones
    response = redirect('desur_menu')  # Cambiar redirect a login de empleados
    response.delete_cookie('uuid')
    return response


# Functions.
"""
def wasap_msg(uid, num):

    import pyautogui
    win = Tk()

    print(num)

    dp = data.objects.filter(fuuid=uid).last()
    if dp:
    {uuid_id = dp.pk
        print{uuid_id)

    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()

    pdfile = Files.objects.filter(fuuid=uid).last()

    if pdfile and pdfile.finalDoc:
        file_path = pdfile.finalDoc.path
        mensaje = "este es el tremendisimo mensaje"

        try:
            pywhatkit.sendwhats_image(
                phone_no=num,
                img_path=file_path,
                caption=mensaje,
                wait_time=15
            )

            pyautogui.moveTo(screen_w/2, screen_h/2)
            pyautogui.click()
            pyautogui.press('enter')
            print("Se mandó el mensaje con todo y todo")
            return redirect('doc')
        except Exception as e:
            print(f"No se pudo enviar nadota: {e}")
            return redirect('doc')
    else:
        print("Sin documentos")
        return redirect('doc')
"""


def gen_folio(uid, puo):
    """Genera folio único para trámites con validaciones mejoradas"""
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
                folio = f'GOP-OFI-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Oficio'
            case 'CRC':
                folio = f'GOP-CRC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'CRC'
            case 'MEC':
                folio = f'GOP-MEC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Marca el cambio'
            case 'DLO':
                folio = f'GOP-DLO-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Diputado Local'
            case 'DFE':
                folio = f'GOP-DFE-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Diputado Federal'
            case 'REG':
                folio = f'GOP-REG-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Regidores'
            case 'DEA':
                folio = f'GOP-DEA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Despacho del Alcalde'
            case 'EVA':
                folio = f'GOP-EVA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Evento con el Alcalde'
            case 'PED':
                folio = f'GOP-PED-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Presencial en Dirección'
            case 'VIN':
                folio = f'GOP-VIN-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Vinculación'
            case 'PPA':
                folio = f'GOP-PPA-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Presupuesto participativo'
            case 'CPC':
                folio = f'GOP-CPC-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'Coordinación de Participación Ciudadana'
            case _:
                folio = f'GOP-VIN-{uuid_id:05d}-{uid_str[:4]}/{year_slice}'
                puo_txt = 'General'

        logger.info(f"Folio generado correctamente: {folio}")
        return puo_txt, folio

    except Exception as e:
        logger.error(f"Error generando folio: {str(e)}")
        return 'Error', f'ERROR-{uid_str[:8]}'

def gen_pp_folio(fuuid):
    """Folio para presupuesto participativo con validaciones mejoradas"""
    try:
        pp_info = PpGeneral.objects.filter(fuuid=fuuid).last()
        uid_str = str(fuuid.uuid)
        id_pp = pp_info.pk if pp_info else 0 # Valor por defecto

        fecha = date.today()
        year_str = str(fecha.year)
        year_slice = year_str[2:4]

        folio = f'GOP-CPP-{id_pp:05d}-{uid_str[:4]}/{year_slice}'

        logger.debug("Folio de PP generado correctamente")
        return folio

    except Exception as e:
        logger.error(f"Error generando folio PP: {str(e)}")
        return f'ERROR-PP-{str(fuuid.uuid)[:8]}'

def validar_curp(curp):
    pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-1A-Z][0-9]$'
    if not re.match(pattern, curp):
        logger.warning("CURP con formato incorrecto detectado")
        raise ValidationError("El formato del CURP es incorrecto.")
    return True

def validar_datos(post_data):
    """
    Valida los datos de entrada del formulario de ciudadanos con validaciones robustas
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
    elif sexo not in ['mujer', 'hombre', 'M', 'H', 'Masculino', 'Femenino']:
        errors.append("El sexo debe ser M (Mujer) o H (Hombre)")

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
    Procesa solicitudes de trámites con validaciones mejoradas y manejo de errores robusto
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
    """Procesa imágenes de solicitudes con validaciones mejoradas"""
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
    """Procesa archivos adjuntos con validaciones"""
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
    """Maneja errores del sistema de forma segura"""
    logger.error(f"Error en vista: {error}", exc_info=True)

    return render(request, 'error.html', {
        'error': {
            'titulo': "Error del sistema",
            'mensaje': 'Por favor, inténtelo nuevamente o contacte al administrador',
            'codigo': 'SYS_ERROR',
            'accion': 'Reintentar'
        }
    })

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

# Presupuesto participativo

@desur_login_required
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

@desur_login_required
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

@desur_login_required
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

@desur_login_required
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

@desur_login_required
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

@desur_login_required
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

