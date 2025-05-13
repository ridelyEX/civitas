from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
import folium
from .models import SubirDocs, soli, data, Contador
from weasyprint import HTML
from django.template.loader import render_to_string


def base(request):
    return render(request, 'base.html')

def nav(request):
    return render(request, 'nav.html')

def home(request):
    return render(request, 'home.html')


def intData(request):
    direccion = request.GET.get('dir', '')
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


        datos = data(
            nombre=nombre,
            pApe=pApe,
            mApe=mApe,
            bDay=bDay,
            asunto=asunto,
            tel=tel,
            curp=curp,
            sexo=sexo,
            dirr=dirr
        )
        datos.save()


        match asunto:
            case "DOP00005":
                return redirect('pago')
            case "DOP00006":
                return redirect('calles')
            case _:
                return redirect('soli')

    context = {
        'dir': direccion,
        'asunto': asunto,
    }
    return render(request, 'di.html', context)


def soliData(request):
        direccion = request.GET.get('dir', '')

        asunto = request.session.get('asunto', '')
        print(asunto)

        if request.method == 'POST':
            dirr = request.POST.get('dir')
            print("Sí es la dirección", dirr)
            descc = request.POST.get('descc')
            if descc is None:
                print("no hay nada")   
            info = request.POST.get('info')
            if info is None:
                print("sin información adicional")
            solicitud = soli(dirr=dirr, descc=descc, info=info)
            solicitud.save()
            return redirect('doc')
        context = {
            'dir':direccion,
            'asunto':asunto,
        }
        return render(request, 'ds.html', context)

def doc(request):
    return render(request, 'dg.html')

def adv(request):
    return render(request, 'adv.html')

def mapa(request):
    origen = request.GET.get('origen', '')
    if request.method == 'GET':
        
        print(origen)
        
    map=folium.Map(location=[28.6403497,-106.0747549], zoom_start=17).add_child(
        folium.LatLngPopup()
    )
    
    return render(request, 'mapa.html', {
        'map':map._repr_html_(),
        'origen': origen,
    })
    
def docs(request):
    documentos = SubirDocs.objects.all().order_by('-nomDoc')
    count = documentos.count()
    if request.method == 'POST':
        contador = Contador(count=count)
        contador.save()
        return redirect('soli')
    return render(request, 'docs.html',{
        'documentos':documentos,
        'count':count,})

def dell(request, id):
    if request.method == 'POST':
        docc = get_object_or_404(SubirDocs, pk=id)
        docc.delete()
        print("se murio")
    return redirect('docs')

def docs2(request):
    if request.method == 'POST' and request.FILES['file']:
        descDoc = request.POST.get('descp')
        docc = request.FILES.get('file')
        nomDoc = docc.name
        documento = SubirDocs(descDoc=descDoc, doc=docc, nomDoc=nomDoc)
        documento.save()
        return redirect('docs')
    else:
        return render(request, 'docs2.html')


def document(request):
    html = render_to_string("documet/document.html")
    pdf_out = HTML(string=html).write_pdf()
    response = HttpResponse(pdf_out, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=información_general.pdf"
    asunto = ''


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

    context = {'asunto':asunto}
    #return response
    return render(request, "documet/document.html")



# Create your views here.
