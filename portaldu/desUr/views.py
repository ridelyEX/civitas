import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
import folium
from .models import SubirDocs, soli, data, Uuid, Pagos, Files
from weasyprint import HTML
from django.template.loader import render_to_string, get_template



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

        uid = get_object_or_404(Uuid, uuid=uuid)
        print(uid)
        direccion = request.GET.get('dir', '')
        asunto = request.session.get('asunto', '')
        print(asunto)
        dp = data.objects.filter(fuuid=uid).last()
        print(dp)

        if request.method == 'POST':
            print(request.method)
            dirr = request.POST.get('dir')
            print("Sí es la dirección", dirr)
            descc = request.POST.get('descc')
            if descc is None:
                print("no hay nada")
            info = request.POST.get('info')
            if info is None:
                print("sin información adicional")
            puo = request.POST.get("puo")
            foto = request.FILES.get('file')
            if foto is None:
                print("no hay nada")

            if dp:
                try:
                    solicitud = soli(data_ID=dp, dirr=dirr, descc=descc, info=info, puo=puo,foto=foto)
                    solicitud.save()
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

            return redirect('doc')

        solicitudes = soli.objects.filter(data_ID=dp)
        context = {
            'dir':direccion,
            'asunto':asunto,
            'uuid':uuid,
            'soli':solicitudes,
            'google_key': settings.GOOGLE_API_KEY,
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
    context = {'asunto': asunto,
               'datos':datos,
               'uuid':uuid}
    return render(request, 'dg.html', context)

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

    if request.method == 'POST' and request.FILES['file']:
        descDoc = request.POST.get('descp')
        docc = request.FILES.get('file')
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

    print(asunto)

    match asunto:
        case "DOP00001":
            asunto = "Arrelgo de calles de terracería - DOP00001"
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
            asunto = "Retiro de escombro y materila de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de material caliche - DOP00011"

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
            "puo" : solicitud.last().puo,
        },
        'documentos':documentos
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
    #if not uuid:
     #   return redirect('home')

    datos = get_object_or_404(data, fuuid__uuid=uuid)
    uid = get_object_or_404(Uuid, uuid=uuid)
    #solicitud = get_object_or_404(soli, data_ID=datos)
    solicitud = soli.objects.filter(data_ID=datos)
    documentos = SubirDocs.objects.filter(fuuid__uuid=uuid).order_by('-nomDoc')

    asunto = request.session.get('asunto', 'Sin asunto')

    print(asunto)

    match asunto:
        case "DOP00001":
            asunto = "Arrelgo de calles de terracería - DOP00001"
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
            asunto = "Retiro de escombro y materila de arrastre - DOP00007"
        case "DOP00008":
            asunto = "Solicitud de material caliche - DOP00008"
        case "DOP00009":
            asunto = "Solicitud de pavimentación de calles - DOP00009"
        case "DOP00010":
            asunto = "Solicitud de reductores de velocidad - DOP00010"
        case "DOP00011":
            asunto = "Solicitud de material caliche - DOP00011"

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
            "puo" : solicitud.last().puo,
        },
        'documentos':documentos
    }
    html = render_to_string("documet/document.html", context)
    buffer = BytesIO()
    pdf_out = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(buffer)
    pdf_file = ContentFile(buffer.getvalue())
    nomDoc = f'VS_{asunto}_{datos.nombre}_{datos.pApe}.pdf'
    doc = Files(nomDoc=nomDoc, fuuid=uid)
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


# Create your views here.
