import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def cleanup_old_logs():
    """
    Tarea para limpiar logs antiguos (más de 30 días)
    """
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    cutoff_date = timezone.now() - timedelta(days=30)

    cleaned_files = 0
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            if os.path.isfile(filepath):
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_modified < cutoff_date.replace(tzinfo=None):
                    try:
                        os.remove(filepath)
                        cleaned_files += 1
                        logger.info(f"Archivo de log eliminado: {filename}")
                    except OSError as e:
                        logger.error(f"Error al eliminar {filename}: {e}")

    logger.info(f"Limpieza de logs completada. Archivos eliminados: {cleaned_files}")
    return {"cleaned_files": cleaned_files}

@shared_task
def send_notification_email(user_email, subject, message, html_message=None):
    """
    Tarea para enviar emails de notificación de forma asíncrona
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email enviado exitosamente a {user_email}")
        return {"status": "success", "email": user_email}
    except Exception as e:
        logger.error(f"Error al enviar email a {user_email}: {str(e)}")
        return {"status": "error", "email": user_email, "error": str(e)}

@shared_task
def process_document_upload(document_id):
    """
    Tarea para procesar documentos subidos de forma asíncrona
    """
    from portaldu.desUr.models import SubirDocs

    try:
        document = SubirDocs.objects.get(doc_ID=document_id)

        # Aquí se pueden agregar validaciones adicionales
        # como escaneo de virus, OCR, etc.

        logger.info(f"Documento procesado exitosamente: {document.nomDoc}")
        return {"status": "success", "document_id": document_id}

    except SubirDocs.DoesNotExist:
        logger.error(f"Documento no encontrado: {document_id}")
        return {"status": "error", "document_id": document_id, "error": "Document not found"}
    except Exception as e:
        logger.error(f"Error al procesar documento {document_id}: {str(e)}")
        return {"status": "error", "document_id": document_id, "error": str(e)}

@shared_task
def generate_reports():
    """
    Tarea para generar reportes periódicos del sistema
    """
    from portaldu.desUr.models import soli, data
    from django.db.models import Count

    try:
        # Estadísticas básicas
        total_solicitudes = soli.objects.count()
        solicitudes_hoy = soli.objects.filter(fecha__date=timezone.now().date()).count()
        total_ciudadanos = data.objects.count()

        # Generar reporte
        report_data = {
            "total_solicitudes": total_solicitudes,
            "solicitudes_hoy": solicitudes_hoy,
            "total_ciudadanos": total_ciudadanos,
            "fecha_reporte": timezone.now().isoformat()
        }

        logger.info(f"Reporte generado: {report_data}")
        return report_data

    except Exception as e:
        logger.error(f"Error al generar reporte: {str(e)}")
        return {"status": "error", "error": str(e)}

@shared_task
def backup_database():
    """
    Tarea para crear respaldos de la base de datos
    """
    import subprocess
    from django.conf import settings

    try:
        db_config = settings.DATABASES['default']
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_civitas_{timestamp}.sql"
        backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_filename)

        # Crear directorio de backups si no existe
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)

        if db_config['ENGINE'] == 'django.db.backends.mysql':
            cmd = [
                'mysqldump',
                f"--host={db_config['HOST']}",
                f"--port={db_config['PORT']}",
                f"--user={db_config['USER']}",
                f"--password={db_config['PASSWORD']}",
                db_config['NAME']
            ]

            with open(backup_path, 'w') as backup_file:
                subprocess.run(cmd, stdout=backup_file, check=True)

        logger.info(f"Backup creado exitosamente: {backup_filename}")
        return {"status": "success", "backup_file": backup_filename}

    except Exception as e:
        logger.error(f"Error al crear backup: {str(e)}")
        return {"status": "error", "error": str(e)}
