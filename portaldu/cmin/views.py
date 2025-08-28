import logging

import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from portaldu.desUr.models import Files, soli
from django.contrib import messages
from django.core.mail import EmailMessage
import os
from .forms import UsersRender, Login, UsersConfig, UploadExcel
from .models import LoginDate, SolicitudesPendientes, SolicitudesEnviadas, Seguimiento, Close, Licitaciones, Users
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger(__name__)

def master(request):
    return render(request, 'master.html')

@login_required
def users_render(request):
    if not request.user.can_manage_users():
        messages.error(request, "No tienes permisos para crear usuarios.")
        return redirect('login')

    if request.method == 'POST':
        print(request.POST)
        form = UsersRender(request.POST, request.FILES, creator_user=request.user)
        if form.is_valid():
            print("estamos dentro")
            try:
                is_staff = form.cleaned_data.get('is_staff', False)
                is_superuser = form.cleaned_data.get('is_superuser', False)

                if not request.user.can_create_user_type(is_staff, is_superuser):
                    user_type = "superusuario" if is_superuser else "staff" if is_staff else "otra cosa"
                    messages.error(request, f"NO tienes permisos para crear {user_type}")
                    return render(request, 'users.html', {'form': form})

                form.save()
                messages.success(request, "Usuario creado correctamente.")
                return redirect('menu')

            except Exception as e:
                messages.error(request, f"Error al crear usuario: {str(e)}")
                return render(request, 'users.html', {'form': form})

    else:
        print("no estamos dentro")
        form = UsersRender(creator_user=request.user)
    return render(request, 'users.html', {'form':form})

def login_view(request):
    form = Login(request.POST)
    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']
        user = authenticate(request, username=usuario, password=contrasena)
        if user is not None:
            try:
                users = Users.objects.get(username=user.username)
                login(request, user)
                LoginDate.objects.create(user_FK=users)

                if user.is_superuser:
                    return redirect('menu')
                elif user.is_staff:
                    return redirect('bandeja_entrada')
            except Users.DoesNotExist:
                logger.error("Usuario no registrado en el sistema.")
                messages.error(request, "Usuario no registrado en el sistema.")
        else:
            logger.error("Usuario o contraseña incorrectos")
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def user_conf(request):
    usuario = request.user
    if request.method == 'POST':
        form = UsersConfig(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('login')
    else:
        form = UsersConfig(instance=usuario)
    return render(request, 'user_conf.html', {'form': form})

def usertest(request):
    return render(request, 'user_conf.html')

@login_required
def tables(request):

    solicitudesG = SolicitudesPendientes.objects.values_list('doc_FK_id', flat=True)
    solicitudesP = Files.objects.exclude(fDoc_ID__in=solicitudesG).order_by('-fDoc_ID')

    solictudesE = SolicitudesEnviadas.objects.all().order_by('-fechaEnvio')

    prioridad_choices = SolicitudesEnviadas.PRIORIDAD_CHOICES
    users = Users.objects.filter(is_staff=True, is_active=True).order_by('username')

    solicitudes = soli.objects.all()

    context = {
        'solicitudesP': solicitudesP,
        'solicitudesE': solictudesE,
        'solicitudes': solicitudes,
        'prioridad_choices': prioridad_choices,
        'users': users,
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

            messages.success(request, "Solicitud guardada")

        except Files.DoesNotExist:
            messages.error(request, "El documento no existe.")
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")

    return redirect('tablas')

@login_required
def seguimiento(request):
    solictudesE = SolicitudesEnviadas.objects.all().order_by('-fechaEnvio')

    solicitudes = soli.objects.all()

    us = ''
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload':
            solicitud_id = request.POST.get('solicitud_id')
            if solicitud_id:
                seguimiento_docs(request, solicitud_id)
        elif action == 'finish':
            solicitud_id = request.POST.get('solicitud_id')
            print(f"Action: {action}")
            print(f"POST data: {request.POST}")
            print(f"Solicitud ID recibido: {solicitud_id}")
            if solicitud_id:
                try:
                    solicitud = get_object_or_404(SolicitudesEnviadas, solicitud_ID=solicitud_id)
                    us = Seguimiento.objects.filter(
                        solicitud_FK=solicitud
                    ).order_by('-fechaSeguimiento').first()

                    # Permitir cerrar solicitudes con o sin seguimiento
                    close = Close.objects.create(
                        solicitud_FK=solicitud,
                        user_FK=request.user,
                        comentario=request.POST.get('comentario', ''),
                        seguimiento_FK=us,  # Puede ser None si no hay seguimiento
                    )

                    if us:
                        print(f"Solicitud cerrada con seguimiento ID: {us.seguimiento_ID}")
                        messages.success(request, "Solicitud cerrada exitosamente con seguimiento.")
                    else:
                        print(f"Solicitud cerrada sin seguimiento previo")
                        messages.success(request, "Solicitud cerrada exitosamente (sin seguimiento previo).")

                except Exception as e:
                    messages.error(request, f"Error al cerrar la solicitud: {str(e)}")
                    print(f"Error al cerrar la solicitud: {str(e)}")
            else:
                print("No se recibió solicitud_id")
                messages.error(request, "No se pudo identificar la solicitud a cerrar")

    context = {
        'solicitudesE': solictudesE,
        'solicitudes': solicitudes,
        'us': us,
    }

    return render(request, 'send.html', context)


@login_required
def menu(request):
    return render(request, 'menu.html')


@login_required
def sendMail(request):
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        correo_destino = request.POST.get('correo')
        msg = request.POST.get('mensaje')
        prioridad = request.POST.get('prioridad', '')
        usuario = request.POST.get('usuario', '')

        usuario_fk = None

        if usuario:
            try:
                usuario_fk = Users.objects.get(username=usuario)
                logger.debug(f"Usuario asignado encontrado: {usuario_fk.username}")
            except Users.DoesNotExist:
                messages.error(request, f"Usuario asignado no encontrado: {usuario}")
                logger.warning(f"Usuario asignado no encontrado: {usuario}")
                return redirect('tablas')

        if not solicitud_id or not correo_destino:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('tablas')

        try:
            documento = Files.objects.get(fDoc_ID=solicitud_id)

            if not documento.soli_FK_id:
                solicitud_existente = soli.objects.filter(data_ID__fuuid=documento.fuuid).first()

                if solicitud_existente:
                    documento.soli_FK = solicitud_existente
                else:
                    from portaldu.desUr.models import data
                    datos = data.objects.filter(fuuid=documento.fuuid).first()

                    if not datos:
                        messages.error(request, "No se encontraron datos asociados al documento.")
                        return redirect('tablas')

                    nueva_solicitud = soli.objects.create(
                        data_ID=datos,
                        dirr="asignación automática",
                        folio=f"AUTO-{documento.fDoc_ID}",
                        doc_ID=documento
                    )
                    documento.soli_FK = nueva_solicitud

                documento.save()

            solicitud = documento.soli_FK
            folio = solicitud.folio if solicitud else None

            solicitud_data = {
                'nomSolicitud': documento.nomDoc or f"Solicitud-{documento.fDoc_ID}",
                'fechaSolicitud': timezone.now().date(),
                'destinatario': correo_destino,
            }


            nommbre_solicitud = documento.nomDoc or f"solicitud-{documento.fDoc_ID}"

            logger.debug(f"Todo se envia {correo_destino}, {documento.nomDoc}, {documento.finalDoc.path}")

            email = EmailMessage(
                subject=f'Solicitud: {nommbre_solicitud}',
                body=msg or f'Se adjunta la solicitud {nommbre_solicitud}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo_destino],
            )

            # Agrega logs para depuración
            print(f"Enviando correo a: {correo_destino}")
            print(f"Documento: {documento.nomDoc}, ID: {documento.fDoc_ID}")
            print(f"Adjunto: {documento.finalDoc.path if documento.finalDoc else 'No hay adjunto'}")


            if documento.finalDoc:
                archivo_path = documento.finalDoc.path
                if os.path.exists(archivo_path):  # Verificar que el archivo existe
                    email.attach_file(archivo_path)
                    print(f"Archivo adjuntado: {archivo_path}")
                else:
                    print(f"El archivo no existe en la ruta: {archivo_path}")
                    messages.warning(request, "El archivo no existe en el sistema.")

            from smtplib import SMTPAuthenticationError, SMTPException
            try:
                email.send(fail_silently=False)  # Cambia a False para ver errores
                logger.debug("Se mandó chido")

                solicitudP, created = SolicitudesPendientes.objects.get_or_create(
                    doc_FK=documento,
                    destinatario=correo_destino,
                    defaults={
                        'nomSolicitud': documento.nomDoc or f"Solicitud-{documento.fDoc_ID}",
                        'fechaSolicitud': timezone.now().date(),
                    }
                )
                solicitud_enviada = SolicitudesEnviadas.objects.create(
                    nomSolicitud=solicitudP.nomSolicitud,
                    user_FK=request.user,
                    doc_FK=documento,
                    solicitud_FK=solicitudP,
                    folio=folio,
                    prioridad=prioridad,
                    usuario_asignado=usuario_fk,
                )
                messages.success(request, f"Correo enviado correctamente a {correo_destino}")
                logger.debug("Correo enviado exitosamente")
            except SMTPAuthenticationError as e:
                logger.error(f"Error de autenticación: {str(e)}")
                messages.error(request, "Error de autenticación con el servidor de correo. Verifica las credenciales.")
                return redirect('tablas')
            except SMTPException as e:
                logger.error(f"Error SMTP: {str(e)}")
                messages.error(request, f"Error SMTP: {str(e)}")
                return redirect('tablas')
            except Exception as e:
                logger.error(f"Error desconocido al enviar: {str(e)}")
                messages.error(request, f"Error al enviar el correo: {str(e)}")
                return redirect('tablas')

        except Files.DoesNotExist:
            messages.error(request, "No se encontró el documento especificado.")
        except Exception as e:
            logger.error(f"Error general: {str(e)}")
            messages.error(request, f"Error al procesar la solicitud: {str(e)}")

    return redirect('tablas')


def seguimiento_docs(request, solicitud_id):
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '')
        nomSeg = request.POST.get('nomSeg', '')

        print(f"Procesando seguimiento para solicitud ID: {solicitud_id}")
        print(f"Comentario: {comentario}")
        print(f"Archivos en request: {list(request.FILES.keys())}")

        if 'documento' in request.FILES:
            archivo = request.FILES['documento']

            # Validar el archivo
            if archivo.size > 5 * 1024 * 1024:  # 5MB
                messages.error(request, "El archivo es demasiado grande. Máximo 5MB.")
                return redirect('seguimiento')

            if not archivo.name.lower().endswith('.pdf'):
                messages.error(request, "Solo se permiten archivos PDF.")
                return redirect('seguimiento')

            try:
                solicitud = get_object_or_404(SolicitudesEnviadas, solicitud_ID=solicitud_id)

                seguimiento = Seguimiento.objects.create(
                    solicitud_FK=solicitud,
                    user_FK=request.user,
                    comentario=comentario,
                    documento=archivo,
                    nomSeg=nomSeg or f"seguimiento_{solicitud_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                )

                messages.success(request, f"Documento de seguimiento guardado correctamente")
                print(f"Seguimiento guardado con ID: {seguimiento.seguimiento_ID}")

            except Exception as e:
                messages.error(request, f"Error al procesar el documento: {str(e)}")
                print(f"Error al guardar seguimiento: {str(e)}")

        else:
            messages.warning(request, "No se ha seleccionado ningún documento")
            print("No se encontró archivo en request.FILES")

    return redirect('seguimiento')

def custom_handler404(request, exception=None):
    context = {}
    return render(request, 'error404.html', context, status=404)


#Excel

def subir_excel(request):
    licitaciones = Licitaciones.objects.all()

    licitaciones.filter(
        fecha_limite__lt=timezone.now().date(),
        activa=True
    ).update(activa=False)

    licitaciones_activas = licitaciones.filter(activa=True)

    if request.method == "POST":
        form = UploadExcel(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['file']
                df = pd.read_excel(excel_file, header=0)

                required_columns = ['Fecha límite', 'No. licitación', 'Descripción']
                for col in required_columns:
                    if col not in df.columns:
                        messages.error(request, f"Columna '{col}' no se encuentra en las tabla")
                        print("no jala")
                        return render(request, 'excel/upload_excel.html', {"form":form,
                                                                                                    "licitaciones": licitaciones_activas})

                for _, row in df.iterrows():
                    Licitaciones.objects.create(
                        fecha_limite=row['Fecha límite'],
                        no_licitacion=row['No. licitación'],
                        desc_licitacion=row['Descripción']
                    )
                messages.success(request, "Archivo de excel subido correctamente")
                return redirect('excel')

            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {str(e)}")
                return render(request, 'excel/upload_excel.html', {"form":form,
                                                                                            "licitaciones": licitaciones_activas})
    else:
        form = UploadExcel()
    return render(request, 'excel/upload_excel.html', {"form":form,
                                                                                "licitaciones": licitaciones_activas})

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff_user, login_url='login')
def bandeja_entrada(request):
    solicitudes_asignadas = SolicitudesEnviadas.objects.filter(
        usuario_asignado=request.user
    ).select_related('doc_FK', 'user_FK', 'solicitud_FK').order_by('-fechaEnvio')

    estado_filtro = request.GET.get('estado', '')
    prioridad_filtro = request.GET.get('prioridad', '')

    if estado_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(estado=estado_filtro)

    if prioridad_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(prioridad=prioridad_filtro)

    stats = {
        'total': solicitudes_asignadas.count(),
        'pendientes': solicitudes_asignadas.filter(estado='pendiente').count(),
        'en_proceso': solicitudes_asignadas.filter(estado='en_proceso').count(),
        'completadas': solicitudes_asignadas.filter(estado='completado').count(),
    }

    context = {
        'solicitudes': solicitudes_asignadas,
        'stats': stats,
        'estado_filtro': estado_filtro,
        'prioridad_filtro': prioridad_filtro,
        'estado_choices': [
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('completado', 'Completado')
        ],
        'prioridad_choices': SolicitudesEnviadas.PRIORIDAD_CHOICES
    }

    return render(request, 'bandeja_entrada.html', context)

@user_passes_test(is_staff_user, login_url='login')
def actualizar_estado_solicitud(request):
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        nuevo_estado = request.POST.get('estado')

        try:
            solicitud = get_object_or_404(
                SolicitudesEnviadas,
                solicitud_ID=solicitud_id,
                usuario_asignado=request.user
            )

            solicitud.estado = nuevo_estado
            solicitud.save()

            messages.success(request, f"Estado actualizado a {nuevo_estado}")

        except Exception as e:
            messages.error(request, f"Error al actualizar estado: {str(e)}")

    return redirect('bandeja_entrada')

"""
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
"""

# Create your views here.
