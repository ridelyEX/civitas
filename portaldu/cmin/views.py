from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from portaldu.desUr.models import Files
from django.contrib import messages
from django.core.mail import EmailMessage
import os
from .forms import UsersRender, Login
from .models import LoginDate, SolicitudesPendientes, SolicitudesEnviadas
import pywhatkit


def master(request):
    return render(request, 'master.html')

def users_render(request):
    if request.method == 'POST':
        print(request.POST)
        form = UsersRender(request.POST, request.FILES)
        if form.is_valid():
            print("estamos dentro")
            cleaned_data = form.cleaned_data
            form.save()
            return redirect('login')
    else:
        print("no estamos dentro")
        form = UsersRender()
    return render(request, 'users.html', {'form':form})


def login_view(request):
    form = Login(request.POST)

    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']
        user = authenticate(request, username=usuario, password=contrasena)
        if user is not None:
            print(user)
            login(request, user)
            LoginDate.objects.create(user_FK=user)
            return redirect('tablas')
        else:
            return HttpResponse("no jalo padre")

    return render(request, 'login.html', {'form':form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def tables(request):


    solicitudesG = SolicitudesPendientes.objects.values_list('doc_FK_id', flat=True)
    solicitudesP = Files.objects.exclude(fDoc_ID__in=solicitudesG).order_by('-fDoc_ID')

    solictudesE = SolicitudesEnviadas.objects.all().order_by('-fechaEnvio')

    context = {
        'solicitudesP': solicitudesP,
        'solicitudesE': solictudesE,
    }

    return render(request, 'tables.html', context)

@login_required
def save_request(request): #saveSoli
    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')
        try:

            documento = Files.objects.get(fDoc_ID=doc_id)

            new_req = SolicitudesPendientes(
                nomSolicitud=documento.nomDoc or f"Solicitud-{documento.fDoc_ID}",
                fechaSolicitud=timezone.now().date(),
                doc_FK=documento
            )

            new_req.save()

            messages.success(request, "SOlicitud guardada")

        except Files.DoesNotExist:
            messages.error(request, "El documento no existe.")
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")
    return redirect('tablas')

@login_required
def sendMail(request): #send_mail
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        correo_destino = request.POST.get('correo')
        msg = request.POST.get('mensaje')

        if not solicitud_id or not correo_destino:
            messages.error(request, "Los campos de solicitud y correo son obligatorios.")
            return redirect('tablas')

        try:
            documento = Files.objects.get(fDoc_ID=solicitud_id)

            solicitudP, created = SolicitudesPendientes.objects.get_or_create(
                doc_FK=documento,
                defaults={
                    'nomSolicitud': documento.nomDoc or f"Solicitud-{documento.fDoc_ID}",
                    'fechaSolicitud': timezone.now().date(),
                }
            )

            email = EmailMessage(
                subject=f'Solicitud: {solicitudP.nomSolicitud}',
                body=msg or f'Se adjunta la soliciut {solicitudP.nomSolicitud}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo_destino],
            )

            if documento.finalDoc:
                archivo_path = documento.finalDoc.path
                email.attach_file(archivo_path)


            from smtplib import SMTPAuthenticationError, SMTPException
            try:

                email.send()
                SolicitudesEnviadas.objects.create(
                    nomSolicitud=solicitudP.nomSolicitud,
                    user_FK=request.user,
                    doc_FK=documento,
                    solicitud_FK=solicitudP
                )
                messages.success(request, f"Correo enviado correctamente a {correo_destino}")
            except SMTPAuthenticationError:
                messages.error(request, "Error de autenticación con el servidor de correo. Verifica las credenciales.")
                return redirect('tablas')
            except SMTPException as e:
                messages.error(request, f"Error SMTP: {str(e)}")
                return redirect('tablas')

            messages.success(request, f"Solicitud Enviada a {correo_destino}")
        except Files.DoesNotExist:
            messages.error(request, "No se pudo enviar nada")
        except Exception as e:
            messages.error(request, f"Error al enviar el correo: {str(e)}")

    return redirect('tablas')


def test_email(request):
    from django.core.mail import send_mail
    import socket
    from smtplib import SMTPAuthenticationError, SMTPException

    try:
        # Prueba la resolución DNS
        socket.gethostbyname('smtp.gmail.com')
        print("✅ Resolución DNS exitosa")

        # Prueba de envío
        send_mail(
            'Prueba de correo Django',
            'Este es un mensaje de prueba desde Django.',
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],  # Envía a ti mismo para pruebas
            fail_silently=False,
        )
        messages.success(request, "Correo enviado correctamente")
        print("✅ Correo enviado")
    except socket.gaierror:
        print("❌ Error de resolución DNS")
        messages.error(request, "Error de conexión: No se puede resolver el servidor SMTP")
    except SMTPAuthenticationError:
        print("❌ Error de autenticación SMTP")
        messages.error(request, "Error de autenticación: Verifica tu usuario y contraseña")
    except SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        messages.error(request, f"Error en el servidor de correo: {str(e)}")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        messages.error(request, f"Error al enviar correo: {str(e)}")

    return redirect('tablas')

def test_wasap(request):

    try:
        import datetime
        hora_envio = datetime.datetime.now()
        envio = hora_envio + datetime.timedelta(minutes=5
                                                )

        hora = envio.hour
        minuto = envio.minute

        pywhatkit.sendwhatmsg("+526142520764", "hola mundo", hora, minuto, 15, True, 10)
        print("se mandó el mensaje")
    except Exception as e:
        print(f"Error al enviar el mensaje: {str(e)}")
        messages.error(request, f"Error al enviar el mensaje: {str(e)}")

    return render(request, 'wasap.html')

# Create your views here.
