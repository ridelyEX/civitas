@echo off
REM Script para ejecutar Celery Worker en Windows

echo Iniciando Celery Worker para Civitas...

REM Activar entorno virtual si existe
if exist "vrtl\Scripts\activate.bat" (
    call vrtl\Scripts\activate.bat
    echo Entorno virtual activado
)

REM Configurar variables de entorno
set DJANGO_SETTINGS_MODULE=civitas.settings

REM Ejecutar Celery Worker
celery -A civitas worker --loglevel=info --pool=solo

pause
