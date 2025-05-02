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
    if request.method == 'POST':
        request.session['datos_formulario'] = request.POST.dict()
        return redirect('soli')
    return render(request, 'di.html')

def soliData(request):
        if request.method == 'POST':
            request.session['datos_solicitud'] = request.POST.dict()
            return redirect('doc')
        return render(request, 'ds.html')

def doc(request):
    return render(request, 'dg.html')

def adv(request):
    return render(request, 'adv.html')

def mapa(request):
    map=folium.Map(location=[28.6403497,-106.0747549], zoom_start=17).add_child(
        folium.ClickForMarker("<b>Lat:</b> ${lat}<br /><b>Lon:</b> ${lng}")
    )
    contexto = request.GET.get('contexto', 'data')
    context = {
        'map':map._repr_html_(),
        'contexto':contexto,
        }
    return render(request, 'mapa.html', context)

# Create your views here.
