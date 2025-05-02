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
    return render(request, 'di.html', {'origen':'data'})

def soliData(request):

        if request.method == 'POST':
            request.session['datos_solicitud'] = request.POST.dict()
            return redirect('doc')
        return render(request, 'ds.html', {'origen':'soli'})

def doc(request):
    return render(request, 'dg.html')

def adv(request):
    return render(request, 'adv.html')

def mapa(request):
    if request.method == 'POST':
        texto = request.POST.get('texto')
        origen = request.POST.get('origen')
        
        
        print(origen)
        print(texto)
        if origen == 'data':
            return redirect('data')
        elif origen == 'soli':
            return redirect('soli')
    map=folium.Map(location=[28.6403497,-106.0747549], zoom_start=17).add_child(
        folium.LatLngPopup()
    )
    
    return render(request, 'mapa.html', {
        'map':map._repr_html_()
    })

# Create your views here.
