import multiprocessing
import os

bind = "unix:/run/civitas/civitas.sock"
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
worker_connections = 1000

timeout = 120
graceful_timeout = 30
keepalive = 5

accesslog = "/home/tstopageo/dev/civitas/logs/gunicorn-access.log"
errorlog = "/home/tstopageo/dev/civitas/logs/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

reload = False
reload_engine = 'auto'

limit_request_line = 4096
limit_request_fields = 100
limit_request_fields_size = 8190

daemon = False
pidfile = "/run/civitas/gunicorn.pid"
umask = 0o007
user = "tstopageo"
group = "www-data"
tmp_upload_dir = None

forwarded_allow_ips = '127.0.0.1, 10.218.6.95, 10.218.3.153'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

def on_starting(server):
    """Ejecutado antes de iniciar el master"""
    server.log.info("Iniciando Gunicorn para AGEO")

def on_reload(server):
    """Ejecutado cuando se recarga"""
    server.log.info("Recargando Gunicorn")

def when_ready(server):
    """Ejecutado cuando el servidor está listo"""
    server.log.info("Gunicorn listo para aceptar conexiones")

def on_exit(server):
    """Ejecutado al salir"""
    server.log.info("Cerrando Gunicorn")

def worker_exit(server, worker):
    """Ejecutado cuando un worker sale"""
    server.log.info(f"Worker {worker.pid} saliendo")

# Pre-fork
preload_app = False
