"""
Vistas del módulo CMIN (Centro de Monitoreo Integral de Notificaciones)
Sistema unificado para la gestión administrativa de solicitudes ciudadanas.

Este módulo contiene todas las vistas principales del sistema CIVITAS - CMIN,
organizadas por funcionalidad y con control de acceso basado en roles.

Roles de usuario:
- administrador: Acceso completo al sistema
- delegado: Gestión y seguimiento de solicitudes
- campo: Acceso limitado a DesUr (redirigido automáticamente)

Dependencias principales:
- Django ORM para gestión de datos
- Django REST Framework para APIs
- Pandas para procesamiento de Excel
- SMTP para envío de correos
"""

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
    Notifications, EncuestasOffline
from django.db.models import Q
from datetime import datetime

# Importaciones para autenticación por token (API REST)
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.core.exceptions import ObjectDoesNotExist

# Utilidad personalizada para manejo de Excel
from .utils.ExcelManager import ExcelManager

# Logger para seguimiento de eventos y errores del sistema
logger = logging.getLogger(__name__)

# === DECORADORES DE SEGURIDAD ===

def role_required(allowed_roles):
    """
    Decorador para verificar que el usuario tenga uno de los roles permitidos.

    Args:
        allowed_roles (list): Lista de roles permitidos para acceder a la vista
                             Valores posibles: ['administrador', 'delegado', 'campo']

    Returns:
        function: Decorador que valida permisos antes de ejecutar la vista

    Funcionalidad:
        - Verifica autenticación del usuario
        - Valida rol contra lista de roles permitidos
        - Redirige según tipo de usuario:
          * No autenticado -> login
          * Rol 'campo' -> módulo DesUr
          * Sin permisos -> menú principal con mensaje de error
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Verificar que el usuario esté autenticado
            if not request.user.is_authenticated:
                return redirect('login')

            # Validar rol del usuario
            if request.user.rol not in allowed_roles:
                messages.error(request, "No tienes permisos para acceder a esta página")
                # Redirigir usuarios de campo al módulo DesUr
                if request.user.rol == 'campo':
                    return redirect('/ageo/home/')
                else:
                    return redirect('menu')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# === VISTAS PRINCIPALES ===

def master(request):
    """
    Vista de página principal/dashboard del sistema.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Renderiza template master.html

    Funcionalidad:
        - Página de bienvenida del sistema
        - Dashboard principal post-login
    """
    return render(request, 'master.html')

def users_render(request):
    """
    Vista para creación de nuevos usuarios del sistema.
    Acceso restringido solo a administradores.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Formulario de creación o redirección según permisos

    Funcionalidad:
        - GET: Muestra formulario de registro
        - POST: Procesa creación de usuario con validaciones
        - Validación de permisos del usuario creador
        - Redirección automática post-creación exitosa
    """
    # Verificar permisos de administrador
    if request.user.is_authenticated and request.user.rol != 'administrador':
        messages.error(request, "No tienes permisos para crear usuarios")
        return redirect('menu')

    if request.method == 'POST':
        # Obtener usuario creador para validación de permisos
        creator_user = request.user if request.user.is_authenticated else None
        form = UsersRender(request.POST, request.FILES, creator_user=request.user)

        if form.is_valid():
            print("estamos dentro")  # Debug: validación exitosa
            cleaned_data = form.cleaned_data
            user = form.save()  # Guardar nuevo usuario con validaciones
            messages.success(request, "Usuario creado exitosamente")
            return redirect('menu')
    else:
        print("no estamos dentro")  # Debug: método GET
        # Preparar formulario vacío con contexto de usuario creador
        creator_user = request.user if request.user.is_authenticated else None
        form = UsersRender(creator_user=creator_user)

    return render(request, 'users.html', {'form': form})

def login_view(request):
    """
    Vista de autenticación unificada para usuarios CMIN y DesUr.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Formulario de login o redirección según autenticación

    Funcionalidad:
        - Sistema de autenticación unificado
        - Migración automática de usuarios legacy
        - Redirección inteligente según rol y permisos:
          * Solo DesUr (campo) -> /desur/
          * Con acceso CMIN -> menú principal
          * Sin permisos -> logout con mensaje
        - Registro automático de fechas de acceso
    """
    if request.method == 'POST':
        form = Login(request.POST)
        if form.is_valid():
            # Extraer credenciales del formulario
            usuario = form.cleaned_data['usuario']
            contrasena = form.cleaned_data['contrasena']
            
            # Usar sistema de autenticación unificado con migración automática
            user = authenticate(request, username=usuario, password=contrasena)
            
            if user is not None:
                # Verificar estado activo de la cuenta
                if not user.is_active:
                    messages.error(request, "Tu cuenta está desactivada. Contacta al administrador.")
                    return render(request, 'login.html', {'form': form})
                
                # Iniciar sesión
                login(request, user)
                
                # Registrar fecha y hora de acceso
                try:
                    LoginDate.objects.create(user_FK=user)
                except Exception as e:
                    logger.warning(f"Error al registrar login para {user.username}: {str(e)}")

                # Redirección inteligente según permisos del usuario
                if user.has_desur_access() and not user.has_cmin_access():
                    # Usuario exclusivo de DesUr (rol campo)
                    return redirect('/ageo/home/')
                elif user.rol == 'delegado':
                    # Usuario con acceso limitado a bandeja de entrada
                    return redirect('bandeja_entrada')
                elif user.has_cmin_access():
                    # Usuario con acceso a CMIN (administrador, delegado)
                    return redirect('menu')
                else:
                    # Usuario sin permisos específicos
                    messages.warning(request, "Tu cuenta no tiene permisos asignados. Contacta al administrador.")
                    logout(request)
                    return render(request, 'login.html', {'form': form})
            else:
                messages.error(request, "Usuario o contraseña incorrectos")
    else:
        # Mostrar formulario de login vacío
        form = Login()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """
    Vista para cerrar sesión del usuario.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponseRedirect: Redirección a página de login

    Funcionalidad:
        - Cierre seguro de sesión
        - Limpieza de datos de sesión
        - Redirección automática al login
    """
    logout(request)
    return redirect('login')

@login_required
def user_conf(request):
    """
    Vista para configuración del perfil personal del usuario.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Formulario de configuración de perfil

    Funcionalidad:
        - GET: Muestra formulario con datos actuales del usuario
        - POST: Procesa actualización de perfil
        - Campos modificables: datos personales, foto, contraseña
        - Validación de cambios y confirmación
    """
    # Obtener instancia del usuario actual
    usuario = request.user

    if request.method == 'POST':
        # Procesar actualización de perfil
        form = UsersConfig(request.POST, request.FILES, instance=usuario)

        # Obtener contraseña
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirmP', '').strip()

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Las contraseñas no coinciden.")
                return render(request, 'user_conf.html', {'form': form})
            if len(password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
                return render(request, 'user_conf.html', {'form': form})

        if form.is_valid():
            user = form.save(commit=False)  # Guardar cambios en la base de datos

            if password:
                user.set_password(password)
                user.save()
                messages.success(request, "Contraseña actualizada correctamente. Por favor, inicia sesión de nuevo.")
                logout(request)
                return redirect('login')
            else:
                user.save()
                messages.success(request, "Perfil actualizado correctamente.")
                return redirect('menu')  # Redirigir al menú principal
        else:
            messages.error(request, "Error al actualizar el perfil. Revisa los datos ingresados.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Mostrar formulario con datos actuales
        form = UsersConfig(instance=usuario)

    return render(request, 'user_conf.html', {'form': form})

def usertest(request):
    """
    Vista de prueba para testing de configuración de usuario.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Template de configuración (solo para testing)
    """
    return render(request, 'user_conf.html')

@login_required
@role_required(['administrador', 'delegado'])
def tables(request):
    """
    Vista principal para gestión de solicitudes.
    Acceso restringido a administradores y delegados.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Panel de gestión con solicitudes pendientes y enviadas

    Funcionalidad:
        - Muestra solicitudes pendientes de procesamiento
        - Lista solicitudes ya enviadas
        - Información de usuarios del staff activos
        - Opciones de prioridad para asignación
        - Acceso a todas las solicitudes del sistema
    """
    # Obtener IDs de solicitudes ya guardadas como pendientes
    solicitudesG = SolicitudesPendientes.objects.values_list('doc_FK_id', flat=True)

    # Filtrar documentos que NO están en solicitudes pendientes
    solicitudesP = Files.objects.exclude(fDoc_ID__in=solicitudesG).order_by('-fDoc_ID')

    # Obtener todas las solicitudes enviadas ordenadas por fecha
    solicitudesE = SolicitudesEnviadas.objects.all().order_by('-fechaEnvio')


    # Opciones de prioridad disponibles para asignación
    prioridad_choices = SolicitudesEnviadas.PRIORIDAD_CHOICES

    # Usuarios del staff activos para asignación de responsables
    users = Users.objects.filter(is_active=True).order_by('username')

    # Todas las solicitudes del sistema
    solicitudes = soli.objects.all()

    # Contexto para el template
    context = {
        'solicitudesP': solicitudesP,        # Solicitudes pendientes de procesar
        'solicitudesE': solicitudesE,        # Solicitudes ya enviadas
        'solicitudes': solicitudes,          # Todas las solicitudes
        'prioridad_choices': prioridad_choices,  # Opciones de prioridad
        'users': users,                      # Usuarios staff para asignación
    }

    return render(request, 'tables.html', context)

@login_required
@role_required(['administrador', 'delegado'])
def save_request(request): #saveSoli
    """
    Vista para guardar nuevas solicitudes en el sistema.
    Acceso restringido a administradores y delegados.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponseRedirect: Redirección a la vista de tablas

    Funcionalidad:
        - Procesa la creación de nuevas solicitudes a partir de documentos
        - Asigna automáticamente folio y nombre a la solicitud
        - Manejo de errores y validaciones
    """
    # Solo administradores y delegados pueden guardar solicitudes
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
@role_required(['administrador', 'delegado'])
def seguimiento(request):
    """
    Vista para gestión de seguimiento de solicitudes.
    Acceso restringido a administradores y delegados.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Panel de seguimiento con filtros y estadísticas

    Funcionalidad:
        - Muestra todas las solicitudes enviadas con opción de seguimiento
        - Permite filtrar por estado, usuario, fecha y prioridad
        - Estadísticas de solicitudes para monitoreo
        - Opción de cerrar solicitudes con o sin seguimiento
    """
    # Solo administradores y delegados pueden hacer seguimiento
    solicitudesE = SolicitudesEnviadas.objects.all().select_related(
        'doc_FK', 'user_FK', 'solicitud_FK', 'usuario_asignado'
    ).prefetch_related('close_set', 'seguimiento_set').order_by('-fechaEnvio')

    solicitudes = soli.objects.all()

    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '').strip()
    estado_filter = request.GET.get('estado', '')
    usuario_filter = request.GET.get('usaurio', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    prioridad_filter = request.GET.get('prioridad', '')

    # Aplicar filtros según parámetros de búsqueda
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
@role_required(['administrador', 'delegado'])
def menu(request):
    """
    Vista del menú principal con acceso restringido por roles"""
    context = {
        'user_role': request.user.rol,
        'can_access_tables': request.user.can_access_tables(),
        'can_access_seguimiento': request.user.can_access_seguimiento(),
        'can_access_admin': request.user.can_access_admin(),
    }
    return render(request, 'menu.html', context)

# ...existing code...

def sendMail(request):
    """
    Vista para envío de correos con solicitudes adjuntas.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponseRedirect: Redirección a la vista de tablas

    Funcionalidad:
        - Procesa el envío de correos a destinatarios específicos
        - Adjunta documentos relacionados a la solicitud
        - Registra el envío en la base de datos
        - Manejo de errores y validaciones
    """
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        correo_destino = request.POST.get('correo')
        msg = request.POST.get('mensaje')
        prioridad = request.POST.get('prioridad', '')
        usuario = request.POST.get('usuario', '')
        categoria = request.POST.get('categorias', '')

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
                    categoria=categoria,
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
    """
    Vista para subir documentos de seguimiento a solicitudes.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        solicitud_id (int): ID de la solicitud a la que se le agrega seguimiento

    Returns:
        HttpResponseRedirect: Redirección a la vista de seguimiento

    Funcionalidad:
        - Procesa la subida de documentos de seguimiento
        - Asocia el documento a la solicitud correspondiente
        - Manejo de errores y validaciones
    """
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

def custom_handler404(request, exception):
    """
    Manejo personalizado de errores 404 (página no encontrada).

    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        exception (Exception): Excepción capturada (opcional)

    Returns:
        HttpResponse: Página de error 404 personalizada

    Funcionalidad:
        - Renderiza una página de error 404 personalizada
        - Contexto puede ser extendido con información adicional
    """
    context = {}
    return render(request, 'error404.html', context, status=404)


#Excel

def subir_excel(request):
    """
    Vista para subir archivos Excel con información de licitaciones.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Formulario de subida de Excel y estado de licitaciones activas

    Funcionalidad:
        - Permite la subida de archivos Excel con datos de licitaciones
        - Valida estructura y columnas requeridas en el archivo
        - Procesa y guarda datos en la base de datos
        - Manejo de errores y mensajes de estado
    """
    licitaciones = Licitaciones.objects.all()

    # Cerrar automáticamente licitaciones pasadas
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

                # Validar columnas requeridas
                required_columns = ['Fecha límite', 'No. licitación', 'Descripción']
                for col in required_columns:
                    if col not in df.columns:
                        messages.error(request, f"Columna '{col}' no se encuentra en las tabla")
                        print("no jala")
                        return render(request, 'excel/upload_excel.html', {"form":form,
                                                                                                    "licitaciones": licitaciones_activas})

                # Procesar cada fila del Excel
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
    """
    Vista para generar y descargar un archivo Excel con reportes completos.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Archivo Excel generado como respuesta de descarga

    Funcionalidad:
        - Genera un archivo Excel con múltiples hojas y datos de diferentes modelos
        - Personaliza formatos y estructuras de acuerdo a requerimientos
        - Manejo de errores y logging de eventos
    """

    modelos = [
        {
            'key': 'ciudadanos',
            'nombre': 'Ciudadanos',
            'modelo': data,
            'campos': {
                'data_ID': 'ID del ciudadano',
                'fuuid': 'UUID',
                'nombre': 'Nombre',
                'pApe': 'Apellido Paterno',
                'mApe': 'Apellido Materno',
                'bDay': 'Fecha de nacimiento',
                'tel': 'Teléfono',
                'curp': 'CURP',
                'sexo': 'Género',
                'asunto': 'Asunto',
                'dirr': 'Dirección',
                'disc': 'Discapacidad',
                'etnia': 'Etnia',
                'vul': 'Grupo vulnerable',
            },
        },
        {
            'key': 'solicitudes',
            'nombre': 'Solicitudes',
            'modelo': soli,
            'campos': {
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
            'key': 'pendientes',
            'nombre': 'Solicitudes Pendientes',
            'modelo': SolicitudesPendientes,
            'campos': {
                'solicitud_ID': 'ID de la solicitud pendiente',
                'nomSolicitud': 'Nombre de la solicitud',
                'fechaSolicitud': 'Fecha de la solicitud',
                'destinatario': 'Destinatario',
            },
        },
        {
            'key': 'enviadas',
            'nombre': 'Solicitudes Enviadas',
            'modelo': SolicitudesEnviadas,
            'campos': {
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

    if request.method == 'POST':
        try:
            response = HttpResponse(
                content_type='application/vnd.opnxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="reporte_completo.xlsx"'

            manager = ExcelManager()

            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                manager.create_formats(writer.book)


                # Procesar cada modelo y generar hojas en el Excel
                for config in modelos:
                    modelo_key = config['key']
                    if not request.POST.get(f'incluir_{modelo_key}'):
                        continue

                    campos_seleccionados = request.POST.getlist(f"campos_{modelo_key}")
                    if not campos_seleccionados:
                        continue

                    try:
                       queryset = config['modelo'].objects.values(*campos_seleccionados)
                       df = pd.DataFrame(list(queryset))

                       if not df.empty:
                           rename_dict = {k: v for k, v in config['campos'].items()
                                          if k in campos_seleccionados}
                           df.rename(columns=rename_dict, inplace=True)
                           manager.process_sheet(df, config['nombre'], writer)
                       else:
                           logger.warning(f"No hay datos en el modeo {config['nombre']}")

                    except Exception as e:
                        logger.error(f"Error en {config['nombre']}: {str(e)}")
                        continue

                return response

        except Exception as e:
            logger.error(f"Error al generar el archivo Excel: {str(e)}")
            messages.error(request, f"Error al generar el archivo excel: {str(e)}")
            return redirect('menu')

    context = {
        'modelos': modelos,
    }

    return render(request, 'excel/import_xlsx.html', context)

#End excel

def is_staff_user(user):
    """
    Verifica si el usuario tiene permisos de staff (administrador o delegado).

    Args:
        user (User): Objeto de usuario a verificar

    Returns:
        bool: True si el usuario es staff, False en caso contrario
    """
    return user.is_authenticated and user.is_staff

@login_required
def bandeja_entrada(request):
    """
    Vista de bandeja de entrada para usuarios con solicitudes asignadas.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Panel de bandeja de entrada con solicitudes y evidencias

    Funcionalidad:
        - Muestra solicitudes asignadas al usuario logueado
        - Permite filtrar por estado y prioridad
        - Muestra evidencias asociadas a cada solicitud
        - Estadísticas de solicitudes para el usuario
    """
    solicitudes_asignadas = SolicitudesEnviadas.objects.filter(
        usuario_asignado=request.user
    ).select_related('doc_FK', 'user_FK', 'solicitud_FK').order_by('-fechaEnvio')
    evidencias = Seguimiento.objects.filter(
        solicitud_FK__in=solicitudes_asignadas
    ).select_related('solicitud_FK', 'user_FK').order_by('-seguimiento_ID', '-fechaSeguimiento')
    evidencia_solicitud = {}

    # Estadísticas de solicitudes
    stats = {
        'total': solicitudes_asignadas.count(),
        'pendientes': solicitudes_asignadas.filter(estado='pendiente').count(),
        'en_proceso': solicitudes_asignadas.filter(estado='en_proceso').count(),
        'completadas': solicitudes_asignadas.filter(estado='completado').count(),
    }

    # Filtros aplicados desde la interfaz
    estado_filtro = request.GET.get('estado', '')
    prioridad_filtro = request.GET.get('prioridad', '')

    if estado_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(estado=estado_filtro)

    if prioridad_filtro:
        solicitudes_asignadas = solicitudes_asignadas.filter(prioridad=prioridad_filtro)


    # Agrupar evidencias por solicitud
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
    """
    Vista para actualizar el estado de una solicitud asignada al usuario.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponseRedirect: Redirección a la bandeja de entrada

    Funcionalidad:
        - Cambia el estado de una solicitud a pendiente, en_proceso o completado
        - Permite adjuntar evidencia al completar una solicitud
        - Manejo de errores y validaciones
    """
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
    """
    Vista para mostrar y gestionar notificaciones del usuario.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP

    Returns:
        HttpResponse: Panel de notificaciones

    Funcionalidad:
        - Muestra notificaciones pendientes y leídas del usuario
        - Marca automáticamente como leídas las notificaciones pendientes
        - Permite interacción con notificaciones (ej. redirección a solicitudes)
    """
    notificaciones = Notifications.objects.filter(user_FK=request.user).order_by('-created_at')

    # Marcar como leídas las notificaciones pendientes
    Notifications.objects.filter(user_FK=request.user, is_read=False).update(is_read=True)

    context = {
        'notificaciones': notificaciones
    }

    return render(request, 'notificaciones.html', context)

@login_required
def marcar_notificacion(request, notificacion_id):
    """
    Vista para marcar una notificación como leída.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        notificacion_id (int): ID de la notificación a marcar como leída

    Returns:
        JsonResponse: Estado de la operación (éxito o error)
    """
    try:
        notificacion = get_object_or_404(Notifications, pk=notificacion_id, user_FK=request.user)
        notificacion.is_read = True
        notificacion.save()
        return JsonResponse({'status':'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def consultar_encuestas(request):
    encuestas_totales = EncuestasOffline.objects.all().order_by('-encuesta_ID')

    # Parámetros de filtros
    search_query = request.GET.get('search', '').strip()
    escuela_filter = request.GET.get('escuelas', '')
    colonia_filter = request.GET.get('colonia', '')
    rol_social_filter = request.GET.get('rol_social', '')
    genero_filter = request.GET.get('genero', '')
    tipo_proyecto_filter = request.GET.get('tipo_proyecto', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    sincronizado_filter = request.GET.get('sincronizado', '')
    completado_filter = request.GET.get('completado', '')

    # Aplicar filtros
    if search_query:
        encuestas = encuestas_totales.filter(
            Q(escuelas__icontains=search_query) |
            Q(colonia__icontains=search_query) |
            Q(f_uuid__icontains=search_query)
        )

    # Filtros por sección
    if escuela_filter:
        encuestas = encuestas_totales.filter(escuelas__icontains=escuela_filter)

    if colonia_filter:
        encuestas = encuestas_totales.filter(colonia__icontains=colonia_filter)

    if rol_social_filter:
        encuesta = encuestas_totales.filter(rol_social=rol_social_filter)

    if genero_filter:
        encuestas = encuestas_totales.filter(genero=genero_filter)

    if tipo_proyecto_filter:
        encuestas = encuestas_totales.filter(tipo_proyecto=tipo_proyecto_filter)

    if fecha_desde:
        encuestas = encuestas_totales.filter(fecha_respuesta__gte=fecha_desde)

    if fecha_hasta:
        encuestas = encuestas_totales.filter(fecha_respuesta__lte=fecha_hasta)

    if sincronizado_filter:
        encuestas = encuestas_totales.filter(sincronizado=int(sincronizado_filter))

    if completado_filter:
        encuestas = encuestas_totales.filter(completada=int(completado_filter))

    # Obtener listas
    escuelas = EncuestasOffline.objects.values_list('escuela', flat=True)
    colonias = EncuestasOffline.objects.values_list('colonia', flat=True)
    roles_sociales = EncuestasOffline.objects.values_list('rol_social', flat=True)
    generos = EncuestasOffline.objects.values_list('genero', flat=True)
    tipos_proyectos = EncuestasOffline.objects.values_list('tipo_proyecto', flat=True)

    # Estadísticas
    total_encuestas = encuestas_totales.count()
    sincronizado = encuestas_totales.filter(sincronizado=1).count()
    no_sincronizadas = encuestas_totales.filter(sincronizado=0).count()
    completadas = encuestas_totales.filter(completada=1).count()
    incompletas = encuestas_totales.filter(completada=0).count()

    por_genero = {}
    for genero in generos:
        if genero:
            por_genero[genero] = encuestas_totales.filter(genero=genero).count()

    context = {
        'encuestas': encuestas_totales,
        'escuelas': escuelas,
        'colonias': colonias,
        'roles_sociales': roles_sociales,
        'generos': generos,
        'tipo_proyecto': tipos_proyectos,

        'search_query': search_query,
        'escuela_filter': escuela_filter,
        'colonia_filter': colonia_filter,
        'rol_social_filter': rol_social_filter,
        'genero_filter': genero_filter,
        'tipo_proyecto_filter': tipo_proyecto_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'sincronizado_filter': sincronizado_filter,
        'completado_filter': completado_filter,

        'stats': {
            'total': total_encuestas,
            'sincronizadas': sincronizado,
            'no_sincronizadas': no_sincronizadas,
            'completadas': completadas,
            'incompletas': incompletas,
            'por_genero': por_genero,
        }
    }
    return render(request, 'encuestas/encuestas_view.html', context)

def detalle_encuesta(request, encuesta_id):
    try:
        encuesta = EncuestasOffline.objects.get(encuesta_ID=encuesta_id)

        def convertir_respuesta(valor):
            respuestas = {
                '0': 'Totalmente en desacuerdo',
                '1': 'En desacuerdo',
                '2': 'Ni de acuerdo ni en desacuerdo',
                '3': 'De acuerdo',
                '4': 'Totalmente de acuerdo',
            }
            return respuestas.get(str(valor), valor)

        def get_value(valor):
            if valor is None or valor == 'None':
                return 'Sin respuesta'
            return valor

        preguntas_map = {
            'pregunta_1': ('¿Estás enterado(a) de que se realizó obra pública en tu comunidad?', convertir_respuesta(encuesta.pregunta_1)),
            'pregunta_2': ('¿Qué tipo de obra fue? (marca una opción si la conoces)', encuesta.pregunta_2),
            'otro_pregunta_2': ('Otro tipo de obra', get_value(encuesta.otro_pregunta_2)),
            'pregunta_3': ('¿Frecuentas o utilizas esa obra?', convertir_respuesta(encuesta.pregunta_3)),
            'pregunta_4': ('¿Estás satisfecho(a) con el resultado y la calidad de la obra pública?', convertir_respuesta(encuesta.pregunta_4)),
            'pregunta_5': ('¿Sabes aproximadamente cuántas personas se benefician con esa obra?', convertir_respuesta(encuesta.pregunta_5)),
            'pregunta_6': ('¿La obra ha mejorado el bienestar y/o calidad de vida o seguridad de niñas, niños y adolescentes o al grupo al que perteneces?', convertir_respuesta(encuesta.pregunta_6)),
            'pregunta_7': ('¿Crees que se pensó en las y los niños, niñas, jóvenes y/o personas vulnerables al hacer la obra?', convertir_respuesta(encuesta.pregunta_7)),
            'pregunta_8': ('¿Consideras que existen suficientes espacios seguros y adecuados para que niños, niñas y adolescentes jueguen o se expresen en tu comunidad?', convertir_respuesta(encuesta.pregunta_8)),
            'pregunta_9': ('¿Los servicios de alud y educación son accesibles para los niños y adolescentes en tu colonia?', convertir_respuesta(encuesta.pregunta_9)),
            'pregunta_10': ('¿Te sientes seguro(a) al caminar por tu colonia?', convertir_respuesta(encuesta.pregunta_10)),
            'pregunta_11': ('¿Es fácil moverte por la ciudad, como caminar, ir en bicicleta o transporte público?', convertir_respuesta(encuesta.pregunta_11)),
            'pregunta_12': ('¿Cuáles consideras que son las necesidades más urgentes de tu comunidad? (Marcar hasta tres opciones)', convertir_respuesta(encuesta.pregunta_12)),
            'otro_pregunta_12': ('Otras necesidades', get_value(encuesta.otro_pregunta_12)),
            'pregunta_13': ('¿Sabías que puedes proponer proyectos comunitarios y votar por ellos?', convertir_respuesta(encuesta.pregunta_13)),
            'pregunta_14': ('¿Conoces cuales son los espacios o formas para expresar las necesidades de tu colonia?', convertir_respuesta(encuesta.pregunta_14)),
            'pregunta_15': ('¿Qué fue lo mejor que trajo la obra pública evaluada?', encuesta.pregunta_15),
            'otro_pregunta_15': ('Otro beneficio', get_value(encuesta.otro_pregunta_15)),
            'pregunta_16': ('¿Qué mejorarías o cambiarías de esa obra?', encuesta.pregunta_16),
            'pregunta_17': ('Si pudieras enviarle un mensaje al alcalde Marco Bonilla sobre las obras públicas, ¿qué le dirías?', get_value(encuesta.pregunta_17)),
        }

        context = {
            'encuesta': encuesta,
            'preguntas': preguntas_map,
        }
        return render(request, 'encuestas/detalle_encuesta.html', context)
    except EncuestasOffline.DoesNotExist:
        messages.error(request, f"Encuesta {encuesta_id} no encontrada")
        return redirect('encuestas')

@receiver(post_save, sender=SolicitudesEnviadas)
def solicitud_notificacion(sender, instance, created, **kwargs):
    """
    Señal para crear notificación al asignar una nueva solicitud.

    Args:
        sender (Model): Modelo que envía la señal
        instance (SolicitudesEnviadas): Instancia de la solicitud enviada
        created (bool): Indica si es una creación nueva

    Funcionalidad:
        - Crea una notificación para el usuario asignado a la solicitud
        - Incluye mensaje y enlace directo a la bandeja de entrada
    """
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
    """
    Señal para crear notificación al agregar un nuevo seguimiento.

    Args:
        sender (Model): Modelo que envía la señal
        instance (Seguimiento): Instancia del seguimiento creado
        created (bool): Indica si es una creación nueva

    Funcionalidad:
        - Crea una notificación para el usuario de la solicitud asociada
        - Incluye mensaje y enlace directo al seguimiento
    """
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
    """
    API para obtener el token de autenticación del usuario.

    Args:
        request (Request): Objeto de solicitud REST

    Returns:
        Response: Token de autenticación o mensaje de error

    Funcionalidad:
        - Autentica al usuario y genera un token de sesión
        - Requiere credenciales válidas (usuario y contraseña)
        - Responde con el token o un mensaje de error
    """
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
