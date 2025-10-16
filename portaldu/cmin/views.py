import logging
import pandas as pd
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.autoreload import template_changed
from django.urls import reverse
from django.utils import timezone
from portaldu.desUr.models import Files, soli, data
from django.contrib import messages
from django.core.mail import EmailMessage
import os
from .forms import UsersRender, Login, UsersConfig, UploadExcel
from .models import LoginDate, SolicitudesPendientes, SolicitudesEnviadas, Seguimiento, Close, Licitaciones, Users, \
    Notifications
from django.db.models import Q
from datetime import datetime

# Autenticación por token
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.core.exceptions import ObjectDoesNotExist

from .utils.ExcelManager import ExcelManager

logger = logging.getLogger(__name__)

# Decoradores para validación de roles
def role_required(allowed_roles):
    """Decorador para verificar que el usuario tenga uno de los roles permitidos"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.rol not in allowed_roles:
                messages.error(request, "No tienes permisos para acceder a esta página")
                if request.user.rol == 'campo':
                    return redirect('/desur/')  # Redirigir a DesUr si es usuario de campo
                else:
                    return redirect('menu')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def master(request):
    return render(request, 'master.html')

def users_render(request):
    # Solo administradores pueden crear usuarios
    if request.user.is_authenticated and request.user.rol != 'administrador':
        messages.error(request, "No tienes permisos para crear usuarios")
        return redirect('menu')

    if request.method == 'POST':
        print(request.POST)
        creator_user = request.user if request.user.is_authenticated else None
        form = UsersRender(request.POST, request.FILES, creator_user=creator_user)
        if form.is_valid():
            print("estamos dentro")
            cleaned_data = form.cleaned_data
            form.save()
            messages.success(request, "Usuario creado exitosamente")
            return redirect('login')
    else:
        print("no estamos dentro")
        creator_user = request.user if request.user.is_authenticated else None
        form = UsersRender(creator_user=creator_user)
    return render(request, 'users.html', {'form':form})

def login_view(request):
    """Vista de login unificada que maneja tanto usuarios de CMIN como DesUr"""
    if request.method == 'POST':
        form = Login(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data['usuario']
            contrasena = form.cleaned_data['contrasena']
            
            # Usar el sistema de autenticación unificado que incluye migración automática
            user = authenticate(request, username=usuario, password=contrasena)
            
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Tu cuenta está desactivada. Contacta al administrador.")
                    return render(request, 'login.html', {'form': form})
                
                login(request, user)
                
                # Registrar el login
                try:
                    LoginDate.objects.create(user_FK=user)
                except Exception as e:
                    logger.warning(f"Error al registrar login para {user.username}: {str(e)}")

                # Redirigir según el rol del usuario y permisos
                if user.has_desur_access() and not user.has_cmin_access():
                    # Usuario solo de DesUr (campo)
                    return redirect('/desur/')
                elif user.has_cmin_access():
                    # Usuario con acceso a CMIN (administrador, delegador)
                    return redirect('menu')
                else:
                    # Usuario sin permisos específicos
                    messages.warning(request, "Tu cuenta no tiene permisos asignados. Contacta al administrador.")
                    logout(request)
                    return render(request, 'login.html', {'form': form})
            else:
                messages.error(request, "Usuario o contraseña incorrectos")
    else:
        form = Login()

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
            return redirect('menu')  # CORREGIR: Redirigir al menú, no al login
    else:
        form = UsersConfig(instance=usuario)
    return render(request, 'user_conf.html', {'form': form})

def usertest(request):
    return render(request, 'user_conf.html')

@login_required
@role_required(['administrador', 'delegador'])
def tables(request):
    # Solo administradores y delegadores pueden ver tablas
    solicitudesG = SolicitudesPendientes.objects.values_list('doc_FK_id', flat=True)
    solicitudesP = Files.objects.exclude(fDoc_ID__in=solicitudesG).order_by('-fDoc_ID')

    solicitudesE = SolicitudesEnviadas.objects.all().order_by('-fechaEnvio')

    prioridad_choices = SolicitudesEnviadas.PRIORIDAD_CHOICES
    users = Users.objects.filter(is_staff=True, is_active=True).order_by('username')

    solicitudes = soli.objects.all()

    context = {
        'solicitudesP': solicitudesP,
        'solicitudesE': solicitudesE,
        'solicitudes': solicitudes,
        'prioridad_choices': prioridad_choices,
        'users': users,
    }

    return render(request, 'tables.html', context)

@login_required
@role_required(['administrador', 'delegador'])
def save_request(request): #saveSoli
    # Solo administradores y delegadores pueden guardar solicitudes
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
@role_required(['administrador', 'delegador'])
def seguimiento(request):
    # Solo administradores y delegadores pueden hacer seguimiento
    solicitudesE = SolicitudesEnviadas.objects.all().select_related(
        'doc_FK', 'user_FK', 'solicitud_FK', 'usuario_asignado'
    ).prefetch_related('close_set', 'seguimiento_set').order_by('-fechaEnvio')

    solicitudes = soli.objects.all()

    search_query = request.GET.get('search', '').strip()
    estado_filter = request.GET.get('estado', '')
    usuario_filter = request.GET.get('usaurio', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    prioridad_filter = request.GET.get('prioridad', '')

    if search_query:
        solicitudesE = solicitudesE.filter(
            Q(nomSolicitud__icontains=search_query) |
            Q(doc_FK__soli_FK__folio__icontains=search_query) |
            Q(solicitud_FK__destinatario__icontains=search_query)
        )

    if estado_filter:
        if estado_filter == 'cerrada':
            solicitudesE = solicitudesE.filter(close__isnull=False)
        elif estado_filter == 'activa':
            solicitudesE = solicitudesE.filter(close__isnull=True)
        elif estado_filter == 'con_seguimiento':
            solicitudesE = solicitudesE.filter(seguimiento__isnull=False)
        elif estado_filter == 'sin_seguimiento':
            solicitudesE = solicitudesE.filter(seguimiento__isnull=True)

    if usuario_filter:
        solicitudesE = solicitudesE.filter(user_FK__username__icontains=usuario_filter)

    if prioridad_filter:
        solicitudesE = solicitudesE.filter(prioridad=prioridad_filter)

    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            solicitudesE = solicitudesE.filter(fechaEnvio__gte=fecha_desde_obj)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            solicitudesE = solicitudesE.filter(fechaEnvio__lte=fecha_hasta_obj)
        except ValueError:
            pass

    #Listas para los filtros
    usuarios_enviadores = Users.objects.filter(
        solicitudesenviadas__isnull=False
    ).distinct().values('username', 'first_name', 'last_name')

    #estadísticas
    total_solicitudes = solicitudesE.count()
    cerradas = solicitudesE.filter(close__isnull=False).count()
    activas = solicitudesE.filter(close__isnull=True).count()
    con_seguimiento = solicitudesE.filter(seguimiento__isnull=False).count()

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
        'solicitudesE': solicitudesE,
        'solicitudes': solicitudes,
        'us': us,
        'usuarios_enviadores': usuarios_enviadores,
        'prioridad_choices': SolicitudesEnviadas.PRIORIDAD_CHOICES,
        'search_query': search_query,
        'estado_filter': estado_filter,
        'usuario_filter': usuario_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'prioridad_filter': prioridad_filter,
        'stats': {
            'total': total_solicitudes,
            'cerradas': cerradas,
            'activas': activas,
            'con_seguimiento': con_seguimiento
        }
    }

    return render(request, 'send.html', context)


@login_required
@role_required(['administrador', 'delegador'])
def menu(request):
    """Vista del menú principal con acceso restringido por roles"""
    context = {
        'user_role': request.user.rol,
        'can_access_tables': request.user.can_access_tables(),
        'can_access_seguimiento': request.user.can_access_seguimiento(),
        'can_access_admin': request.user.can_access_admin(),
    }
    return render(request, 'menu.html', context)

# ...existing code...

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


#Generar excel
def get_excel(request):
    if request.method == 'POST':
        try:
            response = HttpResponse(
                content_type='application/vnd.opnxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="reporte_completo.xlsx"'

            manager = ExcelManager()

            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                manager.create_formats(writer.book)

                modelos = [
                    {
                        'nombre': 'Ciudadanos',
                        'modelo': data,
                        'campos': None,
                        'columns': {
                            'data_ID': 'ID del ciudadano',
                            'fuuid': 'UUID',
                            'nombre': 'Nombre',
                            'apellidoP': 'Apellido Paterno',
                            'apellidoM': 'Apellido Materno',
                            'curp': 'CURP',
                            'bDay': 'Fecha de nacimiento',
                            'sexo': 'Género',
                            'asunto': 'Asunto',
                            'tel': 'Teléfono',
                            'dirr': 'Dirección',
                            'disc': 'Discapacidad',
                            'etnia': 'Etnia',
                            'vul': 'Grupo vulnerable',
                        },
                    },
                    {
                        'nombre': 'Solicitudes',
                        'modelo': soli,
                        'campos': ['soli_ID', 'data_ID__fuuid', 'processed_by', 'dirr', 'descc', 'fecha', 'info', 'puo', 'folio'],
                        'columns': {
                            'soli_ID': 'ID de la solicitud',
                            'data_ID__fuuid': 'UUID del ciudadano',
                            'processed_by': 'Procesado por',
                            'dirr': 'Dirección',
                            'descc': 'Descripción',
                            'fecha': 'Fecha de creación',
                            'info': 'Información adicional',
                            'puo': 'P.U.O',
                            'folio': 'Folio',
                        }
                    },
                    {
                        'nombre': 'Solicitudes Pendientes',
                        'modelo': SolicitudesPendientes,
                        'campos': ['solicitud_ID', 'nomSolicitud', 'fechaSolicitud', 'destinatario'],
                        'columns': {
                            'solicitud_ID': 'ID de la solicitud pendiente',
                            'nomSolicitud': 'Nombre de la solicitud',
                            'fechaSolicitud': 'Fecha de la solicitud',
                            'destinatario': 'Destinatario',
                        },
                    },
                    {
                        'nombre': 'Solicitudes Enviadas',
                        'modelo': SolicitudesEnviadas,
                        'campos': ['solicitud_ID', 'user_FK__username', 'doc_FK', 'solicitud_FK', 'usuario_asignado__username', 'folio', 'categoria', 'prioridad', 'estado', 'fechaEnvio'],
                        'columns': {
                            'solicitud_ID': 'ID de la solicitud enviada',
                            'user_FK__username': 'Usuario que envió',
                            'doc_FK': 'Documento asociado',
                            'solicitud_FK': 'Solicitud pendiente asociada',
                            'usuario_asignado__username': 'Usuario asignado',
                            'folio': 'Folio',
                            'categoria': 'Categoría',
                            'prioridad': 'Prioridad',
                            'estado': 'Estado',
                            'fechaEnvio': 'Fecha de envío',
                        },
                    }
                ]

                for config in modelos:
                    try:
                        if config['campos']:
                            queryset = config['modelo'].objects.values(*config['campos'])
                        else:
                            queryset = config['modelo'].objects.values()

                        df = pd.DataFrame(list(queryset))

                        if not df.empty:
                            rename_dict = {k: v for k, v in config['columns'].items()
                                           if k in df.columns}

                            df.rename(columns=rename_dict, inplace=True)

                            manager.process_sheet(df, config['nombre'], writer)
                        else:
                            logger.warning(f"No hay datos para exportar en {config['nombre']}")

                    except Exception as e:
                        logger.error(f"Error en {config['nombre']}: {str(e)}")
                        continue

                return response

        except Exception as e:
            logger.error(f"Error al generar el archivo Excel: {str(e)}")
            messages.error(request, f"Error al generar el archivo excel: {str(e)}")
            return redirect('menu')

    return render(request, 'excel/import_xlsx.html')

#End excel

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@login_required
def bandeja_entrada(request):
    solicitudes_asignadas = SolicitudesEnviadas.objects.filter(
        usuario_asignado=request.user
    ).select_related('doc_FK', 'user_FK', 'solicitud_FK').order_by('-fechaEnvio')
    evidencias = Seguimiento.objects.filter(
        solicitud_FK__in=solicitudes_asignadas
    ).select_related('solicitud_FK', 'user_FK').order_by('-seguimiento_ID', '-fechaSeguimiento')
    evidencia_solicitud = {}

    stats = {
        'total': solicitudes_asignadas.count(),
        'pendientes': solicitudes_asignadas.filter(estado='pendiente').count(),
        'en_proceso': solicitudes_asignadas.filter(estado='en_proceso').count(),
        'completadas': solicitudes_asignadas.filter(estado='completado').count(),
    }

    estado_filtro = request.GET.get('estado', '')
    prioridad_filtro = request.GET.get('prioridad', '')

    if estado_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(estado=estado_filtro)

    if prioridad_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(prioridad=prioridad_filtro)


    for evidencia in evidencias:
        solicitud_id = evidencia.solicitud_FK.solicitud_ID
        if solicitud_id not in evidencia_solicitud:
            evidencia_solicitud[solicitud_id] = []
        evidencia_solicitud[solicitud_id].append(evidencia)

    context = {
        'solicitudes': solicitudes_asignadas,
        'evidencias': evidencia_solicitud,
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

@login_required
def actualizar_estado_solicitud(request):
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        nuevo_estado = request.POST.get('estado')
        seguimiento = None

        try:
            solicitud = get_object_or_404(
                SolicitudesEnviadas,
                solicitud_ID=solicitud_id,
                usuario_asignado=request.user
            )

            if solicitud.estado == 'completado':
                messages.error(request, "No se puede cambiar el estado de una solicitud completada.")
                return redirect('bandeja_entrada')

            solicitud.estado = nuevo_estado
            solicitud.save()
            if nuevo_estado == 'pendiente':
                messages.success(request, f"Estado actualizado a pendiente")
            elif nuevo_estado == 'en_proceso':
                messages.success(request, f"Estado actualizado a en proceso")
            elif nuevo_estado == 'completado':

                try:
                    evidencia = request.FILES.get('evidencia')
                    nom_evidencia = evidencia.name if evidencia else ''
                    observacion = request.POST.get('observaciones', '')
                    seguimiento = Seguimiento.objects.create(
                        documento=evidencia,
                        nomSeg=nom_evidencia,
                        comentario=observacion if observacion else 'Evidencia de cierre',
                        solicitud_FK=solicitud,
                        user_FK=request.user
                    )
                    seguimiento.save()
                    logger.debug(f"evidencia {observacion}")
                except Exception as e:
                    if nuevo_estado == 'completado':
                        messages.error(request, "No se puede completar sin evidencia.")
                        solicitud.estado = 'en_proceso'
                        solicitud.save()
                        return redirect('bandeja_entrada')
                    else:
                        messages.error(request, f"error: {str(e)}")

                messages.success(request, f"Estado actualizado a completado")

            else:
                print("nada")
                messages.warning(request, "Sin estado cambiado.")

        except Exception as e:
            messages.error(request, f"Error al actualizar estado: {str(e)}")

    return redirect('bandeja_entrada')

"""
Notificaciones Django
"""

@login_required
def notifications(request):
    notificaciones = Notifications.objects.filter(user_FK=request.user).order_by('-created_at')

    Notifications.objects.filter(user_FK=request.user, is_read=False).update(is_read=True)

    context = {
        'notificaciones': notificaciones
    }

    return render(request, 'notificaciones.html', context)

@login_required
def marcar_notificacion(request, notificacion_id):
    try:
        notificacion = get_object_or_404(Notifications, pk=notificacion_id, user_FK=request.user)
        notificacion.is_read = True
        notificacion.save()
        return JsonResponse({'status':'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@receiver(post_save, sender=SolicitudesEnviadas)
def solicitud_notificacion(sender, instance, created, **kwargs):
    if created and instance.usuario_asignado:
        msg = f"Se ha asignado una nueva solicitud: {instance.nomSolicitud}"
        link = reverse('bandeja_entrada')
        Notifications.objects.create(
            user_FK=instance.usuario_asignado,
            msg=msg,
            link=link,
            is_read=False
        )

# Crear notificación al guardar seguimiento
@receiver(post_save, sender=Seguimiento)
def seguimiento_notificacion(sender, instance, created, **kwargs):
    if created:
        solicitud_e = instance.solicitud_FK
        if solicitud_e and solicitud_e.user_FK:
            msg = f"Se ha agregado un nuevo seguimiento a la solicitud '{solicitud_e.nomSolicitud}'."
            link = reverse('seguimiento')
            Notifications.objects.create(
                user_FK=solicitud_e.user_FK,
                msg=msg,
                link=link,
                is_read=False
            )

# Tokens para api de encuestas
@api_view(['post'])
def get_auth_token(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Se requieren ambos campos: username y password'}, status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    else:
        return Response({'error': 'Credenciales inválidas'}, status=401)

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
