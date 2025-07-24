import base64
import uuid
from io import BytesIO
import re
from tempfile import NamedTemporaryFile
import pywhatkit
import googlemaps
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models  # Agregar esta importación para Q
from .models import SubirDocs, soli, data, Uuid, Pagos, Files
from portaldu.cmin.models import Users, LoginDate  # Usar modelos de cmin
from .forms import (DesUrUsersRender, DesUrLogin, DesUrUsersConfig, GeneralRender,
                    ParqueRender, EscuelaRender, CsRender, InfraestructuraRender, PluvialRender)
from django.template.loader import render_to_string, get_template
from weasyprint import HTML
from datetime import date, datetime
from tkinter import *
from rest_framework import viewsets
from .serializers import FilesSerializer


# Vistas de autenticación - PÚBLICAS (obviamente)
def desur_users_render(request):
    # NO login_required - necesario para que administradores creen cuentas de empleados
    if request.method == 'POST':
        print(request.POST)
        form = DesUrUsersRender(request.POST, request.FILES)
        if form.is_valid():
            print("estamos dentro")
            cleaned_data = form.cleaned_data
            form.save()
            return redirect('desur_login')
    else:
        print("no estamos dentro")
        form = DesUrUsersRender()
    return render(request, 'auth/desur_users.html', {'form':form})


def desur_login_view(request):
    # NO login_required - necesario para que empleados inicien sesión
    form = DesUrLogin(request.POST)

    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']
        user = authenticate(request, username=usuario, password=contrasena)
        if user is not None:
            print(user)
            login(request, user)
            LoginDate.objects.create(user_FK=user)  # Usar LoginDate de cmin
            return redirect('desur_menu')  # Ir al menú del empleado
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, 'auth/desur_login.html', {'form':form})


def desur_logout_view(request):
    # NO login_required - aunque podrías argumentar que sí
    logout(request)
    return redirect('desur_login')


@login_required
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


@login_required
def desur_menu(request):
    # SÍ login_required - menú personal
    return render(request, 'auth/desur_menu.html')


@login_required
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


@login_required
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

@login_required
def base(request):
    # SÍ login_required - solo empleados pueden acceder al sistema
    uuid = request.COOKIES.get('uuid')

    if not uuid:
        return redirect('home')
    return render(request, 'documet/save.html',{'uuid':uuid})

@login_required
def home(request):
    # SÍ login_required - punto de entrada solo para empleados autenticados
    if request.method == 'POST':
        uuidM = request.COOKIES.get('uuid')

        if not uuidM:
            uuidM = str(uuid.uuid4())
            new = Uuid(uuid=uuidM)
            new.save()
        else:
            if not Uuid.objects.filter(uuid=uuidM).exists():
                new = Uuid(uuid=uuidM)
                new.save()
                print(new)

        response = redirect('data')
        response.set_cookie('uuid', uuidM, max_age=3600)
        return response
    return render(request, 'main.html')

@login_required
def intData(request):
    # SÍ login_required - empleados capturan datos de ciudadanos
    direccion = request.GET.get('dir', '')
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    print(uuid)

    try:
        uid = get_object_or_404(Uuid, uuid=uuid)
    except:
        return HttpResponse("Sesión inválida"), redirect('home')

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

                if datos_persona['disc']:
                    print("Discapacidad: ", datos_persona['disc'])

                if datos_persona['vul']:
                    print("Discapacidad: ", datos_persona['vul'])

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
            print("Error al procesar los datos:", str(e))
            return HttpResponse('Error al procesar los datos. Vuelva a intentarlo.')

    context = {
        'dir': direccion,
        'asunto': asunto,
        'uuid':uuid,
        'google_key': settings.GOOGLE_API_KEY,
    }
    return render(request, 'di.html', context)


@login_required
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

            print(str(is_mobile) + " " + str(is_tablet) + " " + str(is_pc))

            dir = request.GET.get('dir', '')
            asunto = request.POST.get('asunto', '')
            puo = request.POST.get('puo', '')

            dp = data.objects.select_related('fuuid').filter(fuuid=uid).first()
            if not dp:
                return redirect('home')

            if request.method == 'POST':
                return soli_processed(request, uid, dp)

            solicitud = soli.objects.filter(data_ID=dp).select_related('data_ID')

            context = {
                'dir': dir,
                'asunto': asunto,
                'puo': puo,
                'datos': dp,
                'uuid': uuid,
                'is_mobile': is_mobile,
                'is_tablet': is_tablet,
                'is_pc': is_pc,
                'soli': solicitud,
                'google_key': settings.GOOGLE_API_KEY,
            }

            return render(request, 'ds.html', context)
        except Exception as e:

            return user_errors(request, e)

@login_required
def doc(request):
    # SÍ login_required - empleados gestionan documentación
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = data.objects.filter(fuuid__uuid=uuid).first()
    if not datos:
        HttpResponse("no hay nada")


    asunto = request.session.get('asunto','')
    print(asunto)
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
            elif action == 'wasap':
                wasap_msg(uuid, datos.tel)
    context = {'asunto': asunto,
               'datos':datos,
               'uuid':uuid}
    return render(request, 'dg.html', context)



@login_required
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

@login_required
def dell(request, id):
    # SÍ login_required - empleados eliminan documentos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')
    if request.method == 'POST':
        try:
            docc = get_object_or_404(SubirDocs, pk=id, fuuid__uuid=uuid)
            docc.delete()
            print("se murio")
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método inválido'}, status=405)

@login_required
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


@login_required
def pago(request):
    # SÍ login_required - empleados procesan pagos
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')
    daatos = get_object_or_404(data, fuuid__uuid=uuid)

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        pfm = request.POST.get('pfm')
        pago = Pagos(fecha=fecha, pfm=pfm)
        pago.save()
        return redirect('doc')

    return render(request, 'pago.html')

@login_required
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


@login_required
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

@login_required
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

@login_required
def clear(request):
    # SÍ login_required - solo empleados limpian sesiones
    response = redirect('desur_login')  # Cambiar redirect a login de empleados
    response.delete_cookie('uuid')
    return response


# Functions.

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


def gen_folio(uid, puo):
    print(puo)
    dp = data.objects.filter(fuuid=uid).last()
    uid_str = str(uid.uuid)
    folio = ''
    if dp:
        id_dp = dp.pk
    print(id_dp)
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
    ###
    # Concatenar id al formato del folio y al año
    # Separar la cadena de la fecha?
    # Base de datos para el folio? naahhh
    # ###

    return puo, folio

def cut_direction(dirreccion_completa):
    gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)

    geocode_result = gmaps.geocode(dirreccion_completa)

    if not geocode_result:
        return None, None, None

    calle = None
    colonia = None
    cp = None

    for component in geocode_result[0]['address_components']:
        types = component['types']

        if 'route' in types:
            calle = component['long_name']

            for comp in geocode_result[0]['address_components']:
                if 'street_number' in comp['types']:
                    calle += ' ' + comp['long_name']
                    break

        if any(t in types for t in ['sublocality', 'sublocality_level_1', 'neighborhood']):
            colonia = component['long_name']

        if 'postal_code' in types:
            cp = component['long_name']

    return calle, colonia, cp

def validar_curp(curp):
    pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-1A-Z][0-9]$'
    if pattern != r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-1A-Z][0-9]$':
        print('uhhhhhh Está mal')
        raise ValidationError("El formato del CURP es incorrecto.")


    return bool(re.match(pattern, curp))

def validar_tel(tel):
    pattern = r'^[0-9]{10}$'
    return bool(re.match(pattern, tel))

def validar_datos(request_data):

        errors = []

        mandatory_fields = ['nombre', 'pApe', 'mApe', 'bDay', 'tel', 'curp', 'sexo', 'dir']
        for field in mandatory_fields:
            if not request_data.get(field, '').strip():
                errors.append({
                    'field': field,
                    'mensaje': f'El campo {field} es obligatorio.',
                    'codigo': f'{field.upper()}_required',
                })

        curp = request_data.get('curp', '').strip().upper()
        if curp and not validar_curp(curp):
            errors.append({
                'field': 'curp',
                'mensaje': 'El CURP no es válido.',
                'codigo': 'CURP_invalid'
                })

        tel = request_data.get('tel', '').strip()
        if tel and not validar_tel(tel):
            errors.append({
                'field': 'tel',
                'mensaje': 'El número debe tener 10 digitos.',
                'codigo': 'TEL_FORMAT',
            })

        return errors

def soli_processed(request, uid, dp):
    try:
        with transaction.atomic():
            dirr = request.POST.get('dir')
            print('Dirección: ', dirr)
            calle, colonia, cp = cut_direction(dirr)
            descc = request.POST.get('descc')
            if descc is None:
                print("Sin descripción")

            info = request.POST.get('info')
            if info is None:
                print("Sin información adicional")

            puo = request.POST.get('puo')
            request.session['puo'] = puo

            img = img_processed(request)
            if not img:
                return JsonResponse({'error': 'No hay imagen que rollo'}, status=400)

            solicitud = soli(
                data_ID=dp,
                dirr=dirr,
                calle=calle,
                colonia=colonia,
                cp=cp,
                descc=descc,
                info=info,
                puo=puo,
                foto=img,
                processed_by=request.user  # Registrar qué empleado procesó el trámite
            )

            solicitud.save()
            print("Todo guardado fak yea", solicitud)

            if soli.objects.filter(pk=solicitud.pk).exists():
                print("Solicitud registrada")
            else:
                print("Solicitud no registrada")

            files_processed(request, uid)

            puo_txt, folio = gen_folio(uid, puo)
            solicitud.folio = folio
            solicitud.save()
            print(folio)
            print(puo_txt)

            return redirect('doc')

    except Exception as e:
        print("No se ha guardado nada", str(e))
        return user_errors(request, e)

def img_processed(request):
    img = None
    imgpath = request.POST.get('src')

    if 'src' in request.FILES:
        img = request.FILES['src']
    elif imgpath and imgpath.startswith("data:image"):
        header, encoded = imgpath.split(",", 1)
        datos = base64.b64decode(encoded)
        img = NamedTemporaryFile(delete=False)
        img.write(datos)
        img.flush()
        img = File(img)
    else:
        print("No hay foto, no like")
        return None

    name = str(img.name).split("\\")[-1]
    name += '.jpg'
    img.name = name

    return img

def files_processed(request, uid):
    file_keys = [k for k in request.FILES.keys() if k.startswith('tempfile_')]

    if file_keys:
        for key in file_keys:
            index = key.split('_')[-1]
            file = request.FILES[key]
            desc = request.POST.get(f'tempdesc_{index}')

            if desc is None:
                print("No hay descripción pal documento")
                desc = "Documento sin descripción"

            if not SubirDocs.objects.filter(fuuid=uid, nomDoc=file.name).exists():
                print("no existe documentoc como este, procede a guardarlo papu")
                documento = SubirDocs(
                    descDoc=desc,
                    doc=file,
                    nomDoc=file.name,
                    fuuid=uid,
                )
                documento.save()
            else:
                print("NO se guardará un documento repetido")


def user_errors(request, error):
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error en vista: {error}", exc_info=True)

    return render(request, 'error.html', {
        'error': {
            'titulo': "Error del sistema",
            'mensaje': 'Volver a intentar más tarde',
            'codigo': 'SYS_ERROR',
            'accion': 'Reintentar'
        }
    })

# Presupuesto participativo


def gen_render(request):
    if request.method == 'POST':
        form = GeneralRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = GeneralRender()
    return render(request, 'pp/datos_generales.html', {'form': form})


def escuela_render(request):
    if request.method == 'POST':
        form = EscuelaRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = EscuelaRender()

    return render(request, 'pp/escuela.html', {'form': form})


def parque_render(request):
    if request.method == 'POST':
        form = ParqueRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = ParqueRender()
    return render(request, 'pp/parque.html', {'form': form})


def cs_render(request):
    if request.method == 'POST':
        form = CsRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = CsRender()

    return render(request, 'pp/centro_salon.html', {'form': form})


def infraestructura_render(request):
    if request.method == 'POST':
        form = InfraestructuraRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = InfraestructuraRender()
    return render(request, 'pp/infraestructura.html', {'form': form})


def pluvial_render(request):
    if request.method == 'POST':
        form = PluvialRender(request.POST or None)
        if form.is_valid():
            print("si chambea")
            form.save()
            return redirect('')
    else:
        print("no chambea")
        form = PluvialRender()

    return render(request, 'pp/pluviales.html', {'form': form})


#API
class FilesViewSet(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer
