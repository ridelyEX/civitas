from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.views import View
import folium
from .models import SubirDocs, soli, data


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
    if request.method == 'POST':
        return redirect('soli')
    return render(request, 'docs.html',{'documentos':documentos})

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



# Create your views here.
