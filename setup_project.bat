@echo off
REM Script de inicialización completa para Civitas en Windows

echo ========================================
echo    INICIALIZANDO PROYECTO CIVITAS
echo ========================================

REM Verificar si existe entorno virtual
if not exist "vrtl" (
    echo Creando entorno virtual...
    python -m venv vrtl
)

REM Activar entorno virtual
call vrtl\Scripts\activate.bat
echo Entorno virtual activado

REM Actualizar pip
python -m pip install --upgrade pip

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

REM Crear archivo .env si no existe
if not exist ".env" (
    echo Creando archivo de configuración .env...
    copy .env.example .env
    echo IMPORTANTE: Configura las variables en el archivo .env antes de continuar
    pause
)

REM Crear directorios necesarios
echo Creando directorios...
mkdir logs 2>nul
mkdir backups 2>nul
mkdir staticfiles 2>nul
mkdir media\documents 2>nul
mkdir media\fotos 2>nul
mkdir media\seguimiento_docs 2>nul
mkdir media\solicitudes 2>nul

REM Ejecutar migraciones
echo Ejecutando migraciones de base de datos...
python manage.py makemigrations
python manage.py migrate

REM Crear superusuario (opcional)
echo ¿Deseas crear un superusuario? (s/n)
set /p create_superuser=
if /i "%create_superuser%"=="s" (
    python manage.py createsuperuser
)

REM Recopilar archivos estáticos
echo Recopilando archivos estáticos...
python manage.py collectstatic --noinput

REM Ejecutar tests
echo ¿Deseas ejecutar los tests? (s/n)
set /p run_tests=
if /i "%run_tests%"=="s" (
    echo Ejecutando tests...
    python -m pytest
)

echo ========================================
echo    INICIALIZACIÓN COMPLETADA
echo ========================================
echo Para iniciar el servidor de desarrollo:
echo   python manage.py runserver
echo.
echo Para iniciar Celery Worker:
echo   start_celery_worker.bat
echo.
echo Para iniciar Celery Beat:
echo   start_celery_beat.bat
echo.
echo Documentación de la API disponible en:
echo   http://localhost:8000/swagger/
echo ========================================

pause
