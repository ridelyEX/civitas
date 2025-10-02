@echo off
REM Script para ejecutar Celery Beat (tareas programadas) en Windows

echo Iniciando Celery Beat para Civitas...

REM Activar entorno virtual si existe
if exist "vrtl\Scripts\activate.bat" (
    call vrtl\Scripts\activate.bat
    echo Entorno virtual activado
)

REM Configurar variables de entorno
set DJANGO_SETTINGS_MODULE=civitas.settings

REM Ejecutar Celery Beat
celery -A civitas beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

pause
