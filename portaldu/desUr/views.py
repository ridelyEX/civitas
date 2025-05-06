from django.shortcuts import redirect, render
from django.http import HttpResponse
import folium


def base(request):
    return render(request, 'base.html')

def nav(request):
    return render(request, 'nav.html')

def home(request):
    return render(request, 'home.html')

def intData(request):
    
    direccion = request.GET.get('dir', '')

    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        request.session['asunto'] = asunto
        print(asunto)
        request.session['datos_formulario'] = request.POST.dict()
        return redirect('soli')
    
    context = {
        'dir':direccion,
    }
    return render(request, 'di.html', context)

def soliData(request):
        direccion = request.GET.get('dir', '')

        asunto = request.session.get('asunto', '')
        print(asunto)

        if request.method == 'POST':
            request.session['datos_solicitud'] = request.POST.dict()
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

# Create your views here.
