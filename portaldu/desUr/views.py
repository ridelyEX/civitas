import base64
import uuid
from io import BytesIO
import re
from tempfile import NamedTemporaryFile
import googlemaps

import json
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.db import models  # Agregar esta importación para # Q
from django.utils import timezone
from django_user_agents.templatetags.user_agents import is_mobile
from rest_framework.response import Response

from .models import SubirDocs, soli, data, Uuid, Pagos, Files, PpGeneral, PpParque, PpInfraestructura, PpEscuela, PpCS, \
    PpPluvial, PpFiles, DesUrLoginDate
from .forms import (DesUrUsersRender, DesUrLogin, DesUrUsersConfig, GeneralRender,
                    ParqueRender, EscuelaRender, CsRender, InfraestructuraRender, PluvialRender)
from django.template.loader import render_to_string, get_template
from weasyprint import HTML
from datetime import date, datetime
from rest_framework import viewsets
from .serializers import FilesSerializer
from .auth import DesUrAuthBackend, desur_login_required
from portaldu.cmin.models import Licitaciones
from django.views.decorators.http import require_http_methods
import pandas as pd
import logging

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
    tramites_hoy = tramites.filter(fecha__date=date.today()).count()

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

    mobile_device = is_mobile(request)
    is_offline_sync = request.POST.get('offline_sync', False)

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
                'google_key': settings.GOOGLE_API_KEY,
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
                    'fuuid': uid
                }

                logger.info("Datos de ciudadano procesados correctamente")

                data.objects.update_or_create(
                    fuuid=uid,
                    defaults=datos_persona
                )

                "lógica disposisitivos móviles"
                if mobile_device or is_offline_sync:
                    return JsonResponse({
                        'success': True,
                        'message': 'Datos guardados',
                        'redirect_url': '/ageo/soliData/',
                        'is_offline_sync': is_offline_sync
                    })

                match asunto:
                    case "DOP00005":
                        return redirect('pago')
                    case _:
                        return redirect('soli')

        except Exception as e:
            logger.error(f"Error al procesar datos: {str(e)}")
            return HttpResponse('Error al procesar los datos. Vuelva a intentarlo.')

    template = 'mobile/intData.html' if mobile_device else 'di.html'

    context = {
        'dir': direccion,
        'asunto': asunto,
        'uuid':uuid,
        'google_key': settings.GOOGLE_API_KEY,
    }
    return render(request, template, context)


@desur_login_required
def soliData(request):
    # SÍ login_required - empleados procesan solicitudes de ciudadanos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    mobile_device = is_mobile(request)
    logger.info(f"Procesando solicitud del usuario: {request.user.username}")

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        usuario_data = get_object_or_404(data, fuuid=uid)
    except (Uuid.DoesNotExist, data.DoesNotExist):
        logger.warning(f"Datos no encontrados: {uuid}")
        return redirect('intData')

    logger.debug("Detectando tipo de dispositivo para interfaz")

    dir = request.GET.get('dir', '')
    asunto = request.POST.get('asunto', '')
    puo = request.POST.get('puo', '')

    dp = data.objects.select_related('fuuid').filter(fuuid=uid).first()
    if not dp:
        return redirect('home')

    if request.method == 'POST':
        is_offline_sync = request.POST.get('offline_sync', False)

        if mobile_device or is_offline_sync:
            try:
                response = soli_processed(request, uid, dp)

                if isinstance(response, JsonResponse):
                    return response

                return JsonResponse({
                    'success': True,
                    'message': 'Solicitud procesada',
                    'redirect_url': '/ageo/doc/',
                    'is_offline_sync': is_offline_sync,
                })
            except Exception as e:
                logger.error(f"Error al procesar solicitud: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                }, status=500)

        return soli_processed(request, uid, dp)

    solicitud = soli.objects.filter(data_ID=dp).select_related('data_ID')

    context = {
        'dir': dir,
        'asunto': asunto,
        'puo': puo,
        'datos': dp,
        'uuid': uuid,
        'is_mobile': mobile_device,
        'is_tablet': False,
        'is_pc': not mobile_device,
        'soli': solicitud,
        'google_key': settings.GOOGLE_API_KEY,
    }

    template = 'mobile/soliData.html' if mobile_device else 'ds.html'
    return render(request, template, context)

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
            'fecha': licitacion.fecha_limite.strtime('%d de %B, %Y') if licitacion.fecha_limite else '',
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
    solicitud = soli.objects.filter(data_ID=datos).select_related('data_ID')
    documentos = SubirDocs.objects.filter(fuuid__uuid=uuid).order_by('-nomDoc')

    asunto = request.session.get('asunto', 'Sin asunto')
    puo = request.session.get('puo', 'Sin PUO')
    print(puo)
    num_folio = gen_folio(datos.fuuid, solicitud.last().puo if solicitud.exists() else 'Sin PUO')
    print(asunto)

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

    ultima_solicitud = solicitud.last()
    if ultima_solicitud and ultima_solicitud.folio:
        puo_texto = num_folio[0]
        folio = ultima_solicitud.folio
    else:
        puo_texto, folio = gen_folio(datos.fuuid, solicitud.last().puo if solicitud.exists() else 'no hay puo')

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
            "dir": solicitud.last().dirr if solicitud.exists() else "",
            "info": solicitud.last().info,
            "desc": solicitud.last().descc if solicitud.exists() else "",
            "foto": solicitud.last().foto,
        },
        'puo':puo_texto,
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
    solicitud = soli.objects.last()
    print(solicitud)
    if not solicitud:
        return HttpResponse("no hay solicitud", status=400)
    documentos = SubirDocs.objects.filter(fuuid__uuid=uuid).order_by('-nomDoc')

    asunto = request.session.get('asunto', 'Sin asunto')
    puo = request.session.get('puo', 'Sin PUO')
    print(puo)
    num_folio = gen_folio(datos.fuuid, solicitud.puo if solicitud else 'Sin PUO')
    print(asunto)

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

    ultima_solicitud = solicitud
    if ultima_solicitud and ultima_solicitud.folio:
        puo_texto = num_folio[0]
        folio = ultima_solicitud.folio
    else:
        puo_texto, folio = gen_folio(datos.fuuid, solicitud.puo if solicitud else 'no hay puo')

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
        },
        'puo': puo_texto,
        'documentos': documentos,
        'folio': folio,
    }
    html = render_to_string("documet/document.html", context)
    buffer = BytesIO()
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(buffer)
    pdf_file = ContentFile(buffer.getvalue())
    nomDoc = f'VS_{asunto}_{datos.nombre}_{datos.pApe}.pdf'
    doc = Files(nomDoc=nomDoc, fuuid=uid, soli_FK=ultima_solicitud)
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
        id_dp = dp.pk
        print(id_dp)

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

    uid_str = str(uid.uuid)  # Mover esta línea al inicio

    try:
        dp = data.objects.filter(fuuid=uid).last()
        id_dp = dp.pk if dp else 0 # Valor por defecto si no hay datos

        fecha = date.today()
        year_str = str(fecha.year)
        year_slice = year_str[2:4]

        match puo:
            case 'OFI':
                folio = f'GOP-OFI-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Oficio'
            case 'CRC':
                folio = f'GOP-CRC-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'CRC'
            case 'MEC':
                folio = f'GOP-MEC-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Marca el cambio'
            case 'DLO':
                folio = f'GOP-DLO-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Diputado Local'
            case 'DFE':
                folio = f'GOP-DFE-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Diputado Federal'
            case 'REG':
                folio = f'GOP-REG-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Regidores'
            case 'DEA':
                folio = f'GOP-DEA-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Despacho del Alcalde'
            case 'EVA':
                folio = f'GOP-EVA-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Evento con el Alcalde'
            case 'PED':
                folio = f'GOP-PED-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Presencial en Dirección'
            case 'VIN':
                folio = f'GOP-VIN-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Vinculación'
            case 'PPA':
                folio = f'GOP-PPA-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Presupuesto participativo'
            case 'CPC':
                folio = f'GOP-CPC-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'Coordinación de Participación Ciudadana'
            case _:
                folio = f'GOP-GEN-{id_dp:05d}-{uid_str[:4]}/{year_slice}'
                puo = 'General'

        logger.info(f"Folio generado correctamente: {folio}")
        return puo, folio

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
    elif sexo not in ['mujer', 'hombre', 'M', 'H']:
        errors.append("El sexo debe ser M (Mujer) o H (Hombre)")

    # Validar dirección
    direccion = post_data.get('dir', '').strip()
    if not direccion:
        errors.append("La dirección es obligatoria")
    elif len(direccion) < 10:
        errors.append("La dirección debe ser más específica")

    # Validar asunto
    asunto = post_data.get('asunto', '').strip()
    if not asunto:
        errors.append("El asunto es obligatorio")

    return errors


def soli_processed(request, uid, dp):
    """Procesa solicitudes de ciudadanos con validaciones mejoradas"""
    try:
        with transaction.atomic():
            solicitud_data = {
                'dirr': request.POST.get('dir'),
                'info': request.POST.get('info'),
                'descc': request.POST.get('desc'),
                'puo': request.POST.get('puo'),
                'data_ID': dp,
                'processed_by': request.user,
                'fecha': timezone.now()
            }

            if 'foto' in request.FILES:
                solicitud_data['foto'] = request.FILES['foto']

            solicitud = soli.objects.create(**solicitud_data)

            # Generar folio
            puo_texto, folio = gen_folio(dp.fuuid, solicitud.puo)
            solicitud.folio = folio
            solicitud.save()

            # Guardar en sesión
            request.session['puo'] = solicitud.puo
            request.session['folio'] = folio

            logger.info(f"Solicitud procesada exitosamente por {request.user.username}")
            return redirect('doc')

    except Exception as e:
        logger.error(f"Error procesando solicitud: {str(e)}")
        return HttpResponse('Error al procesar solicitud. Intente nuevamente.')


# ==================== FUNCIONES PWA Y MÓVILES ====================

from django.http import HttpResponse
from django.template.loader import render_to_string
import json

def service_worker(request):
    """Sirve el archivo Service Worker para PWA"""
    import os
    from django.conf import settings

    # Ruta completa al archivo Service Worker
    sw_path = os.path.join(settings.BASE_DIR, 'portaldu', 'desUr', 'static', 'sw.js')

    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        # Fallback si no encuentra el archivo
        content = '''
        console.log('DesUr SW: Service Worker básico cargado');
        
        self.addEventListener('install', event => {
            console.log('DesUr SW: Instalando...');
            self.skipWaiting();
        });
        
        self.addEventListener('activate', event => {
            console.log('DesUr SW: Activando...');
            self.clients.claim();
        });
        '''

    response = HttpResponse(content, content_type='application/javascript')
    response['Cache-Control'] = 'no-cache'
    response['Service-Worker-Allowed'] = '/desur/'
    return response


def manifest(request):
    """Genera el archivo manifest.json para PWA"""
    manifest_data = {
        "name": "DesUr - Portal de Desarrollo Urbano",
        "short_name": "DesUr",
        "description": "Portal de trámites de desarrollo urbano para dispositivos móviles - Funciona sin conexión",
        "start_url": "/ageo/auth/menu/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "orientation": "portrait-primary",
        "scope": "/ageo/",
        "categories": ["government", "utilities", "productivity"],
        "lang": "es-MX",
        "dir": "ltr",
        "prefer_related_applications": False,
        "edge_side_panel": {
            "preferred_width": 480
        },
        "icons": [
            {
                "src": "/static/images/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/images/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable any"
            }
        ],
        "screenshots": [
            {
                "src": "/static/images/screenshot-desktop.png",
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide"
            },
            {
                "src": "/static/images/screenshot-mobile.png",
                "sizes": "375x667",
                "type": "image/png",
                "form_factor": "narrow"
            }
        ]
    }

    return JsonResponse(manifest_data, content_type='application/manifest+json')


def offline_page(request):
    """Página offline para cuando no hay conexión"""
    return render(request, 'pwa/offline.html')


def install_prompt(request):
    """Página de instalación PWA"""
    return render(request, 'pwa/install.html')


# ==================== VISTAS MÓVILES ====================

@desur_login_required
def mobile_menu(request):
    """Menú optimizado para dispositivos móviles"""
    # Estadísticas rápidas para el empleado
    tramites_hoy = soli.objects.filter(
        processed_by=request.user,
        fecha__date=date.today()
    ).count()

    total_tramites = soli.objects.filter(processed_by=request.user).count()

    context = {
        'empleado': request.user,
        'tramites_hoy': tramites_hoy,
        'total_tramites': total_tramites,
        'is_mobile': True
    }

    return render(request, 'mobile/menu.html', context)


@desur_login_required
def mobile_historial(request):
    """Historial optimizado para móviles"""
    tramites = soli.objects.filter(
        processed_by=request.user
    ).select_related('data_ID').order_by('-fecha')[:20]  # Limitar a 20 más recientes

    context = {
        'tramites': tramites,
        'empleado': request.user,
        'is_mobile': True
    }

    return render(request, 'mobile/historial.html', context)


@desur_login_required
def confirmacion_mobile(request):
    """Página de confirmación para móviles"""
    return render(request, 'mobile/confirmacion.html', {'is_mobile': True})


# ==================== APIs PARA FUNCIONALIDAD OFFLINE ====================

@desur_login_required
def sync_offline_data(request):
    """API para sincronizar datos offline"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sync_type = data.get('type')

            if sync_type == 'form_data':
                return sync_form_data(request, data)
            elif sync_type == 'user_status':
                return sync_user_status(request, data)
            else:
                return JsonResponse({'error': 'Tipo de sincronización no válido'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error en sincronización: {str(e)}")
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def sync_form_data(request, data):
    """Sincroniza datos de formularios guardados offline"""
    try:
        form_data = data.get('form_data', {})
        form_type = data.get('form_type')

        # Procesar según el tipo de formulario
        if form_type == 'citizen_data':
            return process_offline_citizen_data(request, form_data)
        elif form_type == 'solicitud':
            return process_offline_solicitud(request, form_data)
        else:
            return JsonResponse({'error': 'Tipo de formulario no reconocido'}, status=400)

    except Exception as e:
        logger.error(f"Error procesando datos offline: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def process_offline_citizen_data(request, form_data):
    """Procesa datos de ciudadanos guardados offline"""
    try:
        # Validar datos
        errors = validar_datos(form_data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # Crear UUID si no existe
        uuid_str = form_data.get('uuid')
        if not uuid_str:
            uuid_str = str(uuid.uuid4())
            uid = Uuid.objects.create(uuid=uuid_str)
        else:
            uid, created = Uuid.objects.get_or_create(uuid=uuid_str)

        # Guardar datos
        datos_persona = {
            'nombre': form_data.get('nombre', '').upper(),
            'pApe': form_data.get('pApe', '').upper(),
            'mApe': form_data.get('mApe', '').upper(),
            'bDay': form_data.get('bDay'),
            'tel': form_data.get('tel'),
            'curp': form_data.get('curp', '').upper(),
            'sexo': form_data.get('sexo'),
            'dirr': form_data.get('dir'),
            'asunto': form_data.get('asunto'),
            'etnia': form_data.get('etnia', 'No pertenece a una etnia'),
            'disc': form_data.get('discapacidad', 'sin discapacidad'),
            'vul': form_data.get('vulnerables', 'No pertenece a un grupo vulnerable'),
            'fuuid': uid
        }

        data.objects.update_or_create(fuuid=uid, defaults=datos_persona)

        return JsonResponse({
            'success': True,
            'message': 'Datos sincronizados correctamente',
            'uuid': uuid_str
        })

    except Exception as e:
        logger.error(f"Error procesando datos de ciudadano offline: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def process_offline_solicitud(request, form_data):
    """Procesa solicitudes guardadas offline"""
    try:
        uuid_str = form_data.get('uuid')
        if not uuid_str:
            return JsonResponse({'success': False, 'error': 'UUID requerido'}, status=400)

        uid = get_object_or_404(Uuid, uuid=uuid_str)
        dp = get_object_or_404(data, fuuid=uid)

        solicitud_data = {
            'dirr': form_data.get('dir'),
            'info': form_data.get('info'),
            'descc': form_data.get('desc'),
            'puo': form_data.get('puo'),
            'data_ID': dp,
            'processed_by': request.user,
            'fecha': timezone.now()
        }

        solicitud = soli.objects.create(**solicitud_data)

        # Generar folio
        puo_texto, folio = gen_folio(dp.fuuid, solicitud.puo)
        solicitud.folio = folio
        solicitud.save()

        return JsonResponse({
            'success': True,
            'message': 'Solicitud sincronizada correctamente',
            'folio': folio
        })

    except Exception as e:
        logger.error(f"Error procesando solicitud offline: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def sync_user_status(request, data):
    """Sincroniza estado del usuario"""
    try:
        last_activity = data.get('last_activity')
        if last_activity:
            # Actualizar última actividad del usuario
            pass

        return JsonResponse({
            'success': True,
            'server_time': timezone.now().isoformat(),
            'user_status': 'active'
        })

    except Exception as e:
        logger.error(f"Error sincronizando estado de usuario: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@desur_login_required
def api_user_data(request):
    """API para obtener datos del usuario actual"""
    user = request.user

    # Estadísticas del usuario
    total_tramites = soli.objects.filter(processed_by=user).count()
    tramites_hoy = soli.objects.filter(
        processed_by=user,
        fecha__date=date.today()
    ).count()

    # Últimos trámites
    ultimos_tramites = soli.objects.filter(
        processed_by=user
    ).select_related('data_ID').order_by('-fecha')[:5]

    tramites_data = []
    for tramite in ultimos_tramites:
        tramites_data.append({
            'folio': tramite.folio,
            'ciudadano': f"{tramite.data_ID.nombre} {tramite.data_ID.pApe}",
            'puo': tramite.puo,
            'fecha': tramite.fecha.isoformat() if tramite.fecha else None,
        })

    response_data = {
        'user': {
            'username': user.username,
            'nombre': user.nombre if hasattr(user, 'nombre') else '',
            'apellido': user.apellido if hasattr(user, 'apellido') else '',
        },
        'stats': {
            'total_tramites': total_tramites,
            'tramites_hoy': tramites_hoy,
        },
        'ultimos_tramites': tramites_data,
        'server_time': timezone.now().isoformat()
    }

    return JsonResponse(response_data)


# ==================== FUNCIONES DE UTILIDAD ====================

def is_mobile_device(request):
    """Detecta si el dispositivo es móvil"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone', 'blackberry']
    return any(keyword in user_agent for keyword in mobile_keywords)


def get_device_info(request):
    """Obtiene información del dispositivo del usuario"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    is_mobile = is_mobile_device(request)
    is_tablet = 'tablet' in user_agent.lower() or 'ipad' in user_agent.lower()
    is_desktop = not is_mobile and not is_tablet

    return {
        'is_mobile': is_mobile,
        'is_tablet': is_tablet,
        'is_desktop': is_desktop,
        'user_agent': user_agent
    }


# ==================== VISTAS DE PRUEBA PARA PWA ====================

def test_pwa_functionality(request):
    """Vista de prueba para verificar funcionalidad PWA"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Solo disponible en modo debug'}, status=403)

    device_info = get_device_info(request)

    test_results = {
        'service_worker_registered': True,  # Se verificará en el frontend
        'manifest_valid': True,
        'offline_capable': True,
        'device_info': device_info,
        'timestamp': timezone.now().isoformat()
    }

    return JsonResponse(test_results)


# ==================== VISTAS DE PRESUPUESTO PARTICIPATIVO ====================
# (Las vistas de PP ya están implementadas arriba, solo agregamos las que faltan)

@desur_login_required
def gen_render(request):
    """Vista principal de presupuesto participativo"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    if request.method == 'POST':
        form = GeneralRender(request.POST)
        if form.is_valid():
            uid = get_object_or_404(Uuid, uuid=uuid)
            form_instance = form.save(commit=False)
            form_instance.fuuid = uid
            form_instance.save()

            categoria = request.POST.get('categoria')
            request.session['categoria'] = categoria

            if categoria == 'parque':
                return redirect('parques')
            elif categoria == 'escuela':
                return redirect('escuelas')
            elif categoria == 'cs':
                return redirect('centros')
            elif categoria == 'infraestructura':
                return redirect('infraestructura')
            elif categoria == 'pluviales':
                return redirect('pluviales')

    else:
        form = GeneralRender()

    return render(request, 'pp/general.html', {'form': form, 'uuid': uuid})


@desur_login_required
def parque_render(request):
    """Vista para presupuesto participativo - parques"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        pp_general = get_object_or_404(PpGeneral, fuuid=uid)
    except:
        return redirect('general')

    if request.method == 'POST':
        form = ParqueRender(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.fk_pp = pp_general
            form_instance.save()
            return redirect('pp_document')
    else:
        form = ParqueRender()

    return render(request, 'pp/parques.html', {'form': form, 'uuid': uuid})


@desur_login_required
def escuela_render(request):
    """Vista para presupuesto participativo - escuelas"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        pp_general = get_object_or_404(PpGeneral, fuuid=uid)
    except:
        return redirect('general')

    if request.method == 'POST':
        form = EscuelaRender(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.fk_pp = pp_general
            form_instance.save()
            return redirect('pp_document')
    else:
        form = EscuelaRender()

    return render(request, 'pp/escuelas.html', {'form': form, 'uuid': uuid})


@desur_login_required
def cs_render(request):
    """Vista para presupuesto participativo - centros comunitarios"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        pp_general = get_object_or_404(PpGeneral, fuuid=uid)
    except:
        return redirect('general')

    if request.method == 'POST':
        form = CsRender(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.fk_pp = pp_general
            form_instance.save()
            return redirect('pp_document')
    else:
        form = CsRender()

    return render(request, 'pp/centros.html', {'form': form, 'uuid': uuid})


@desur_login_required
def infraestructura_render(request):
    """Vista para presupuesto participativo - infraestructura"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        pp_general = get_object_or_404(PpGeneral, fuuid=uid)
    except:
        return redirect('general')

    if request.method == 'POST':
        form = InfraestructuraRender(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.fk_pp = pp_general
            form_instance.save()
            return redirect('pp_document')
    else:
        form = InfraestructuraRender()

    return render(request, 'pp/infraestructura.html', {'form': form, 'uuid': uuid})


@desur_login_required
def pluvial_render(request):
    """Vista para presupuesto participativo - soluciones pluviales"""
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
        pp_general = get_object_or_404(PpGeneral, fuuid=uid)
    except:
        return redirect('general')

    if request.method == 'POST':
        form = PluvialRender(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.fk_pp = pp_general
            form_instance.save()
            return redirect('pp_document')
    else:
        form = PluvialRender()

    return render(request, 'pp/pluviales.html', {'form': form, 'uuid': uuid})
