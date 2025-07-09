import base64
import uuid
from io import BytesIO
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import pywhatkit
from django.core.files import File
import googlemaps
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from .models import SubirDocs, soli, data, Uuid, Pagos, Files
from weasyprint import HTML
from django.template.loader import render_to_string, get_template
from datetime import date
from tkinter import *


def base(request):
    uuid = request.COOKIES.get('uuid')

    if not uuid:
        return redirect('home')
    return render(request, 'documet/save.html',{'uuid':uuid})

def nav(request):
    return render(request, 'navmin.html')

def clear(request):
    response = redirect('home')
    response.delete_cookie('uuid')
    return response

def home(request):
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


def intData(request):
    direccion = request.GET.get('dir', '')
    uuid = request.COOKIES.get('uuid')


    print(uuid)

    uid = get_object_or_404(Uuid, uuid=uuid)

    asunto = ''

    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        request.session['asunto'] = asunto


        nombre = request.POST.get('nombre')
        pApe = request.POST.get('pApe')
        mApe = request.POST.get('mApe')
        bDay = request.POST.get('bDay')
        tel = request.POST.get('tel')
        curp = request.POST.get('curp')
        sexo = request.POST.get('sexo')
        dirr = request.POST.get('dir')
        etnia = request.POST.get('etnia')
        print(etnia)
        if etnia is None:
            print("sin etnia")
            etnia = "sin etnia"
        disc = request.POST.get('discapacidad')
        if disc is None:
            print("normal")
            disc = "sin discapacidad"

        if not data.objects.filter(fuuid=uid).exists():
            datos = data(
                nombre=nombre,
                pApe=pApe,
                mApe=mApe,
                bDay=bDay,
                asunto=asunto,
                tel=tel,
                curp=curp,
                sexo=sexo,
                dirr=dirr,
                fuuid=uid,
                etnia=etnia,
                disc=disc
            )
            datos.save()
        else:
            print("ya hay datos")
            data.objects.update_or_create(
                fuuid=uid,
                defaults={
                    'nombre' : nombre,
                    'pApe' : pApe,
                    'mApe' : mApe,
                    'bDay' : bDay,
                    'asunto' : asunto,
                    'tel' : tel,
                    'curp' : curp,
                    'sexo' : sexo,
                    'dirr' : dirr,
                    'etnia' : etnia,
                    'disc' : disc,
                    }
                )

        match asunto:
            case "DOP00005":
                return redirect('pago')
            case _:
                return redirect('soli')

    context = {
        'dir': direccion,
        'asunto': asunto,
        'uuid':uuid,
        'google_key': settings.GOOGLE_API_KEY,
    }
    return render(request, 'di.html', context)


def soliData(request):
        uuid = request.COOKIES.get('uuid')
        if not uuid:
            return redirect('home')

        is_mobile = request.user_agent.is_mobile
        is_tablet = request.user_agent.is_tablet
        is_pc = request.user_agent.is_pc

        puo = ''
        solicitud = ''
        uid = get_object_or_404(Uuid, uuid=uuid)
        print(uid)
        direccion = request.GET.get('dir', '')
        asunto = request.session.get('asunto', '')
        print(asunto)
        dp = data.objects.filter(fuuid=uid).last()
        if dp:
            id_dp = dp.pk
        print(id_dp)
        context = dict()
        if request.method == 'POST':
            print(request.method)
            dirr = request.POST.get('dir')
            print("Sí es la dirección", dirr)
            calle, colonia, cp = cut_direction(dirr)
            descc = request.POST.get('descc')
            if descc is None:
                print("no hay nada")
            info = request.POST.get('info')
            if info is None:
                print("sin información adicional")
            puo = request.POST.get("puo")
            request.session['puo'] = puo
            img = None
            imgpath = request.POST.get("src")
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
                print("No hay imagen")
                return JsonResponse({'error': 'sin imagen'}, status=400)
            name = str(img.name).split("\\")[-1]
            name += '.jpg'
            img.name = name
            #foto = request.FILES.get('file')

            if dp and img is not None:
                try:
                    solicitud = soli(data_ID=dp,
                                     dirr=dirr,
                                     calle=calle,
                                     colonia=colonia,
                                     cp=cp,
                                     descc=descc,
                                     info=info,
                                     puo=puo,
                                     foto=img,
                                     )
                    solicitud.save()
                    context['imgpath'] = solicitud.foto.url
                    print("se guardó todo", solicitud)

                    if soli.objects.filter(pk=solicitud.pk).exists():
                        print("registrado")
                    else:
                        print("no registrado")
                except Exception as e:
                    print("no se guarda fakin nada", str(e))
            else:
                print("no hay fakin nada ni en dp")

            file_keys = [k for k in request.FILES.keys() if k.startswith('tempfile_')]

            if file_keys:
                for key in file_keys:
                    index = key.split('_')[-1]
                    file = request.FILES[key]
                    desc = request.POST.get(f'tempdesc_{index}')
                    if desc is None:
                        print("no hay descripción del documento")
                        desc = "Documento sin descripción"

                    if not SubirDocs.objects.filter(fuuid=uid, nomDoc=file.name).exists():
                        print("no existe el documento, se guardará")
                    else:
                        print("el documento ya existe, no se guardará de nuevo")
                    documento = SubirDocs(
                        descDoc=desc,
                        doc=file,
                        nomDoc=file.name,
                        fuuid=uid
                        )
                    documento.save()

            puo_texto, folio = gen_folio(uid, puo)
            solicitud.folio = folio
            solicitud.save()
            print(folio)
            print(puo_texto)

            return redirect('doc')

        solicitudes = soli.objects.filter(data_ID=dp)
        context = {
            'dir':direccion,
            'asunto':asunto,
            'uuid':uuid,
            'soli':solicitudes,
            'google_key': settings.GOOGLE_API_KEY,
            'puo': puo,
            'is_mobile': is_mobile,
            'is_tablet': is_tablet,
            'is_pc': is_pc,
        }
        return render(request, 'ds.html', context)

def doc(request):
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
    ###
    # Concatenar id al formato del folio y al año
    # Separar la cadena de la fecha?
    # Base de datos para el folio? naahhh
    # ###

    return puo, folio

def adv(request):
    return render(request, 'adv.html')

def mapa(request):

    origen = request.GET.get('origen', '')
    if request.method == 'GET':

        print(origen)
    return render(request, 'mapa.html', {
        'google_key':settings.GOOGLE_API_KEY,
        'origen': origen,
    })
    
def docs(request):
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

def dell(request, id):
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

def docs2(request):
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


def pago(request):
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

def document(request):
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = get_object_or_404(data, fuuid__uuid=uuid)
    #solicitud = get_object_or_404(soli, data_ID=datos)
    solicitud = soli.objects.filter(data_ID=datos)
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
            asunto = "Limpieza de arrollos al sur de la ciudad - DOP00003"
        case "DOP00004":
            asunto = "Limpieza o mantenimiento de rejillas pluviales - DOP00004"
        case "DOP00005":
            asunto = "Pago de costo de participación en licitaciones de obra pública - DOP00005"
        case "DOP00006":
            asunto = "Rehabilitación de calles - DOP00006"
        case "DOP00007":
            asunto = "Retiro de escombro y material de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de material caliche - DOP00011"

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


def save_document(request):
    uuid = request.COOKIES.get('uuid')
    if not uuid:
        return redirect('home')

    datos = get_object_or_404(data, fuuid__uuid=uuid)
    uid = get_object_or_404(Uuid, uuid=uuid)
    #solicitud = get_object_or_404(soli, data_ID=datos)
    solicitud = soli.objects.last()
    print(solicitud)
    if not solicitud:
        return HttpResponse("no hay sikucitud", status=400)
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
            asunto = "Limpieza de arrollos al sur de la ciudad - DOP00003"
        case "DOP00004":
            asunto = "Limpieza o mantenimiento de rejillas pluviales - DOP00004"
        case "DOP00005":
            asunto = "Pago de costo de participación en licitaciones de obra pública - DOP00005"
        case "DOP00006":
            asunto = "Rehabilitación de calles - DOP00006"
        case "DOP00007":
            asunto = "Retiro de escombro y material de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de material caliche - DOP00011"

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

def document2(request):
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




# Create your views here.
