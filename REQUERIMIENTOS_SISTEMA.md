# REQUERIMIENTOS DEL SISTEMA CIVITAS
## Especificaciones Técnicas para Despliegue

### 📋 INFORMACIÓN GENERAL
- **Nombre del Sistema**: Civitas - Portal de Trámites Ciudadanos
- **Versión**: 1.0
- **Arquitectura**: Aplicación Web Django con dos módulos (DesUr y CMIN)
- **Fecha de especificación**: Agosto 2025

---

## 🖥️ SISTEMA OPERATIVO

### Sistemas Operativos Compatibles (por orden de recomendación):

#### **PRODUCCIÓN (Recomendado)**
- **Ubuntu Server 22.04 LTS** o superior
- **CentOS 8** / **Rocky Linux 8+** / **AlmaLinux 8+**
- **Debian 11** (Bullseye) o superior
- **Red Hat Enterprise Linux 8+**

#### **DESARROLLO/TESTING**
- **Windows 10/11** (como se evidencia en el desarrollo actual)
- **macOS 12+** (Monterey)
- **Ubuntu Desktop 22.04+**

#### **CONTENEDORES**
- **Docker** en cualquier SO compatible
- **Kubernetes** para despliegues escalables

---

## 💾 ESPACIO EN DISCO

### **Mínimo Requerido**
- **Sistema base**: 10 GB
- **Aplicación y dependencias**: 2 GB
- **Base de datos**: 5 GB (inicial)
- **Archivos media (documentos/fotos)**: 20 GB
- **Logs del sistema**: 2 GB
- **Backups**: 15 GB
- **TOTAL MÍNIMO**: **54 GB**

### **Recomendado para Producción**
- **Sistema base**: 50 GB
- **Aplicación**: 5 GB
- **Base de datos**: 100 GB (con crecimiento)
- **Archivos media**: 200 GB
- **Logs**: 10 GB
- **Backups**: 100 GB
- **Espacio libre**: 50 GB
- **TOTAL RECOMENDADO**: **515 GB**

### **Distribución de Almacenamiento**
```
/var/lib/mysql/          - Base de datos MySQL/PostgreSQL
/opt/civitas/media/      - Archivos subidos por usuarios
/opt/civitas/static/     - Archivos estáticos
/var/log/civitas/        - Logs de aplicación
/backup/civitas/         - Respaldos automáticos
```

---

## 🧠 MEMORIA RAM

### **Configuración Mínima**
- **RAM Total**: 4 GB
- **Distribución**:
  - Sistema operativo: 1 GB
  - Base de datos: 1 GB
  - Aplicación Django: 1 GB
  - Servidor web: 512 MB
  - Disponible: 512 MB

### **Configuración Recomendada para Producción**
- **RAM Total**: 16 GB
- **Distribución**:
  - Sistema operativo: 2 GB
  - Base de datos (MySQL/PostgreSQL): 6 GB
  - Aplicación Django (múltiples workers): 4 GB
  - Servidor web (Nginx): 1 GB
  - Cache/Redis: 2 GB
  - Disponible: 1 GB

### **Configuración Óptima (Alto Tráfico)**
- **RAM Total**: 32 GB o superior
- **Configuración escalable** con balanceadores de carga

---

## ⚡ PROCESADORES

### **Mínimo**
- **CPU**: 2 núcleos / 2 threads
- **Arquitectura**: x86_64 (64-bit)
- **Frecuencia**: 2.0 GHz mínimo

### **Recomendado para Producción**
- **CPU**: 4 núcleos / 8 threads
- **Arquitectura**: x86_64
- **Frecuencia**: 2.4 GHz o superior
- **Ejemplos**:
  - Intel Core i5 8ª generación o superior
  - AMD Ryzen 5 3600 o superior
  - Intel Xeon E-2236 o superior

### **Óptimo (Alto Rendimiento)**
- **CPU**: 8+ núcleos / 16+ threads
- **Frecuencia**: 3.0 GHz o superior
- **Cache L3**: 16 MB o superior

---

## 💻 LENGUAJES Y TECNOLOGÍAS

### **Lenguaje Principal**
- **Python**: 3.11+ (recomendado 3.12)
- **Compatibilidad**: 3.9 mínimo, 3.13 máximo

### **Framework Web**
- **Django**: 5.2 (actual)
- **Django REST Framework**: Para APIs

### **Base de Datos**
#### **Desarrollo**
- **MySQL**: 8.0+ (configuración actual)
- **Configuración**: localhost:3306

#### **Producción (Recomendado)**
- **PostgreSQL**: 14+ (preferido para producción)
- **MySQL**: 8.0+ (alternativa)

### **Servidor Web**
- **Nginx**: 1.20+ (proxy reverso)
- **Gunicorn**: 20.1+ (servidor WSGI)

### **Dependencias Python Principales**
```txt
Django >= 4.2, <= 5.0
python-dotenv >= 0.19.0
django-bootstrap5 >= 22.2
django-user-agents >= 0.4.0
django-phonenumber-field >= 7.0.0
phonenumbers >= 8.12.0
pywhatkit >= 5.4
Pillow >= 9.0.0
gunicorn >= 20.1.0
psycopg2-binary >= 2.9.0 (para PostgreSQL)
pandas (para análisis de datos)
```

---

## 🔧 SOFTWARE ADICIONAL REQUERIDO

### **Servidor Web y Proxy**
- **Nginx**: 1.20+
- **Certificados SSL**: Let's Encrypt recomendado

### **Base de Datos**
- **MySQL Server**: 8.0+ O **PostgreSQL**: 14+

### **Gestión de Procesos**
- **systemd** (Linux)
- **Supervisor** (alternativa)

### **Monitoreo (Opcional pero Recomendado)**
- **htop** / **top**: Monitoreo de recursos
- **fail2ban**: Seguridad
- **logrotate**: Gestión de logs

---

## 📊 ESTIMACIONES DE RENDIMIENTO

### **Usuarios Concurrentes Soportados**
- **Configuración mínima**: 50 usuarios
- **Configuración recomendada**: 500 usuarios
- **Configuración óptima**: 2000+ usuarios

### **Tiempo de Respuesta Esperado**
- **Páginas estáticas**: < 200ms
- **Consultas de base de datos**: < 500ms
- **Subida de archivos**: Variable según tamaño

---

## 🔒 CONSIDERACIONES DE SEGURIDAD

### **Sistema Operativo**
- Actualizaciones de seguridad automáticas
- Firewall configurado (ufw/iptables)
- Usuarios sin privilegios para la aplicación

### **Aplicación**
- Variables de entorno para credenciales
- HTTPS obligatorio en producción
- Backups automáticos diarios

---

## 📋 CHECKLIST DE INSTALACIÓN

### **Pre-instalación**
- [ ] Verificar requerimientos de hardware
- [ ] Sistema operativo actualizado
- [ ] Python 3.11+ instalado
- [ ] Base de datos configurada

### **Instalación**
- [ ] Clonar repositorio
- [ ] Crear entorno virtual
- [ ] Instalar dependencias
- [ ] Configurar variables de entorno
- [ ] Ejecutar migraciones
- [ ] Configurar servidor web
- [ ] Configurar SSL

### **Post-instalación**
- [ ] Pruebas de funcionalidad
- [ ] Configurar backups
- [ ] Monitoreo activo
- [ ] Documentación de accesos

---

## 🔧 CONFIGURACIONES ESPECÍFICAS

### **Variables de Entorno Requeridas**
```bash
# Seguridad
SECRET_KEY=tu_clave_secreta_muy_segura_aqui
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos
DB_ENGINE=django.db.backends.postgresql
DB_NAME=civitas_prod
DB_USER=civitas_user
DB_PASSWORD=password_muy_seguro
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# APIs
GOOGLE_MAPS_API_KEY=tu_api_key_de_google_maps
```

### **Configuración de Nginx**
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tu-dominio.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /static/ {
        alias /opt/civitas/staticfiles/;
    }
    
    location /media/ {
        alias /opt/civitas/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 MONITOREO Y RENDIMIENTO

### **Métricas Clave a Monitorear**
- **CPU**: Uso promedio < 70%
- **RAM**: Uso < 80%
- **Disco**: Espacio libre > 20%
- **Red**: Latencia < 100ms
- **Base de datos**: Consultas < 500ms
- **Aplicación**: Tiempo respuesta < 2s

### **Herramientas de Monitoreo**
- **htop/top**: Monitoreo de recursos
- **mysqladmin**: Estado de MySQL
- **Django Debug Toolbar**: Desarrollo
- **Prometheus + Grafana**: Producción avanzada

---

## 🔒 SEGURIDAD

### **Configuraciones de Seguridad Obligatorias**
- **SSL/TLS**: Certificado válido
- **Firewall**: Solo puertos necesarios abiertos
- **Fail2ban**: Protección contra ataques de fuerza bruta
- **Backup automatizado**: Diario mínimo
- **Actualizaciones**: Parches de seguridad mensuales

### **Validaciones de Datos**
- **CSRF Protection**: Habilitado
- **XSS Protection**: Headers configurados
- **SQL Injection**: Queries parametrizadas
- **File Upload**: Validación de tipos y tamaños

---

## 📝 CHECKLIST PRE-DESPLIEGUE

### ✅ **Configuración Obligatoria**
- [ ] SECRET_KEY única generada
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configurado
- [ ] Base de datos de producción
- [ ] Variables de entorno configuradas
- [ ] SSL certificado instalado
- [ ] Backup configurado

### ✅ **Pruebas Requeridas**
- [ ] Migraciones de BD exitosas
- [ ] Archivos estáticos servidos
- [ ] Upload de archivos funcional
- [ ] Envío de emails operativo
- [ ] Sistema de auth funcional
- [ ] Formularios validados

### ✅ **Optimizaciones**
- [ ] Cache Redis configurado
- [ ] Compresión de archivos estáticos
- [ ] Logs rotación configurada
- [ ] Monitoreo implementado
