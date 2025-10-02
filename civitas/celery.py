import os
from celery import Celery
from django.conf import settings

# Configurar Django settings para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civitas.settings')

app = Celery('civitas')

# Usar string para evitar problemas de serialización
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrimiento de tareas en todas las apps de Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configuración adicional de Celery
app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
)
