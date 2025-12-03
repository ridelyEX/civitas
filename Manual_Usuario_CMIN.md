# Manual de Usuario - Sistema CIVITAS - Módulo CMIN

## Tabla de Contenidos
1. [Introducción al Sistema CIVITAS - Módulo CMIN](#introducción-al-sistema-CIVITAS---módulo-cmin)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Panel Principal](#panel-principal)
4. [Gestión de Solicitudes](#gestión-de-solicitudes)
5. [Seguimiento de Trámites](#seguimiento-de-trámites)
6. [Comunicación con Ciudadanos](#comunicación-con-ciudadanos)
7. [Configuración de Perfil](#configuración-de-perfil)
8. [Preguntas Frecuentes](#preguntas-frecuentes)
9. [Documentación Técnica - Vistas y API](#documentación-técnica---vistas-y-api)

---

## Introducción al Sistema CIVITAS - Módulo CMIN

CIVITAS - Módulo CMIN es una plataforma diseñada para la **gestión integral de solicitudes ciudadanas** en el municipio. Este sistema permite a los funcionarios municipales revisar, procesar y dar seguimiento a todas las solicitudes generadas desde el sistema DesUr, manteniendo una comunicación efectiva con los ciudadanos a través de notificaciones por email.

### Funcionalidades Principales:
- **Revisión de solicitudes pendientes** generadas desde DesUr
- **Gestión de solicitudes enviadas** a otras dependencias
- **Seguimiento completo** del estado de trámites
- **Comunicación automática** vía email con ciudadanos
- **Cierre y finalización** de procesos administrativos
- **Historial completo** de todas las gestiones realizadas
- **Gestión de documentos** de seguimiento

### Diferencia con AGEO:
- **AGEO:** Captura inicial de solicitudes ciudadanas
- **AGEO - admin:** Procesamiento, seguimiento y comunicación posterior
- **CIVITAS - CMIN:** Gestión integral, incluyendo asignación de prioridades, envío de correos masivos y generación de reportes avanzados

---

## Acceso al Sistema

### 1. Pantalla de Inicio de Sesión

![Pantalla de Login CMIN](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.34%20AM.jpeg)

Para acceder al sistema CIVITAS - Módulo CMIN, utilice sus credenciales de funcionario municipal:

**Campos requeridos:**
- **Usuario:** Su nombre de usuario asignado
- **Contraseña:** Su contraseña personal

**Opciones disponibles:**
- **Botón "Iniciar Sesión"**: Para acceder al sistema
- **Enlace "Crear Cuenta"**: Para registro de nuevos usuarios (solo administradores)

### 2. Registro de Nuevos Funcionarios

![Pantalla de Registro](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.34%20AM%20(1).jpeg)

La pantalla de registro permite crear cuentas para nuevos funcionarios:

**Información requerida:**
- **Nombre de usuario**
- **Email institucional**
- **Contraseña segura**
- **Confirmación de contraseña**
- **Fecha de nacimiento**
- **Fotografía oficial**

---

## Panel Principal

### 3. Menú Principal del Sistema

![Menú Principal CMIN](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM.jpeg)

Una vez autenticado, accederá al panel principal de CIVITAS - Módulo CMIN:

#### **Opciones Principales:**
- **📋 Gestión de Solicitudes**: Revisar y procesar nuevas solicitudes
- **📊 Seguimiento**: Monitorear el estado de trámites en proceso
- **📧 Comunicaciones**: Enviar notificaciones a ciudadanos
- **⚙️ Configuración**: Ajustes de perfil personal
- **📈 Reportes**: Estadísticas y análisis de gestión

#### **Panel de Estado:**
- **Solicitudes Pendientes**: Cantidad de trámites por revisar
- **En Proceso**: Solicitudes actualmente en seguimiento
- **Finalizadas**: Trámites completados en el período

---

## Gestión de Solicitudes

### 4. Panel de Solicitudes Pendientes

![Solicitudes Pendientes](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM%20(1).jpeg)

Esta pantalla muestra todas las solicitudes generadas desde DesUr que requieren procesamiento:

**Información mostrada:**
- **ID de Solicitud**: Número único del trámite
- **Fecha de Creación**: Cuándo se generó la solicitud
- **Ciudadano**: Nombre del solicitante
- **Tipo de Trámite**: Categoría de la solicitud
- **Documentos**: Archivos adjuntos disponibles
- **Estado**: Pendiente, En Proceso, Finalizado

**Acciones disponibles:**
- **👁️ Ver Detalles**: Revisar información completa
- **✅ Aceptar**: Procesar la solicitud
- **📧 Enviar**: Comunicar al ciudadano
- **📎 Documentos**: Ver archivos adjuntos

### 5. Procesamiento de Solicitudes

![Procesamiento de Solicitudes](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM%20(2).jpeg)

Al seleccionar una solicitud para procesar:

**Pasos del proceso:**
1. **Revisión de Documentos**: Verificar que la documentación esté completa
2. **Asignación de Folio**: El sistema genera un número único de seguimiento
3. **Clasificación**: Determinar la dependencia responsable
4. **Envío**: Transferir la solicitud para atención especializada

**Campos editables:**
- **Destinatario**: Dependencia que atenderá el trámite
- **Observaciones**: Comentarios del funcionario
- **Prioridad**: Nivel de urgencia del trámite
- **Fecha estimada**: Tiempo proyectado de resolución

---

## Seguimiento de Trámites

### 6. Panel de Seguimiento

![Panel de Seguimiento](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM%20(3).jpeg)

Esta sección permite monitorear el progreso de todas las solicitudes en proceso:

**Información de seguimiento:**
- **Folio**: Número único del trámite
- **Estado Actual**: Fase en que se encuentra
- **Responsable**: Funcionario asignado
- **Última Actualización**: Fecha del último movimiento
- **Tiempo Transcurrido**: Días desde el inicio

**Estados posibles:**
- 🟡 **Pendiente**: Esperando asignación
- 🔵 **En Proceso**: Siendo atendido por la dependencia
- 🟢 **Resuelto**: Trámite completado
- 🔴 **Requerimiento**: Necesita información adicional

### 7. Actualización de Estado

![Actualización de Estado](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM%20(4).jpeg)

Para actualizar el progreso de un trámite:

**Acciones disponibles:**
- **📝 Agregar Comentario**: Registrar avances o incidencias
- **📎 Subir Documento**: Adjuntar evidencia del progreso
- **📧 Notificar Ciudadano**: Enviar actualización automática
- **✅ Marcar como Completado**: Finalizar el trámite

**Campos del seguimiento:**
- **Fecha**: Automática del sistema
- **Funcionario**: Usuario que realiza la actualización
- **Comentario**: Descripción del avance o incidencia
- **Documento**: Archivo de respaldo (opcional)

---

## Comunicación con Ciudadanos

### 8. Sistema de Notificaciones

![Sistema de Notificaciones](capturas%20cmin/WhatsApp%20Image%202025-08-01%20at%209.47.35%20AM%20(5).jpeg)

CIVITAS - Módulo CMIN incluye un sistema automatizado de comunicación con los ciudadanos:

**Tipos de notificaciones automáticas:**
- **Confirmación de recepción**: Al recibir la solicitud
- **Asignación de folio**: Cuando se procesa inicialmente
- **Actualizaciones de estado**: En cada cambio significativo
- **Solicitud de información**: Si se requieren datos adicionales
- **Notificación de resolución**: Al completar el trámite

**Personalización de mensajes:**
- **Plantillas predefinidas** para cada tipo de comunicación
- **Variables automáticas** (nombre, folio, fecha, etc.)
- **Firma institucional** estándar
- **Información de contacto** para consultas

---

## Configuración de Perfil

### 9. Gestión de Perfil Personal

Los funcionarios pueden actualizar su información personal desde el sistema:

**Datos modificables:**
- **Información de contacto** personal
- **Fotografía de perfil** oficial
- **Contraseña** de acceso
- **Configuraciones de notificaciones**
- **Firma digital** para comunicaciones

**Seguridad:**
- **Cambio de contraseña** periódico recomendado
- **Autenticación de dos factores** (si está habilitada)
- **Registro de accesos** para auditoría

---

## Flujo Completo del Sistema

### Proceso Integral: De AGEO a AGEO - admin

1. **En AGEO**: El ciudadano genera una solicitud con todos sus datos
2. **Transferencia automática**: La solicitud llega a AGEO - admin como "Pendiente"
3. **En AGEO - admin**: El funcionario revisa y procesa la solicitud
4. **Asignación**: Se genera folio y se envía a la dependencia responsable
5. **Seguimiento**: Se monitorea el progreso del trámite
6. **Comunicación**: Se mantiene informado al ciudadano
7. **Cierre**: Se finaliza el proceso y se archiva

---

## Reportes y Estadísticas

### Análisis de Gestión

El sistema CIVITAS - Módulo CMIN genera automáticamente:

**Reportes disponibles:**
- **Solicitudes por período** (diario, semanal, mensual)
- **Tiempo promedio de resolución** por tipo de trámite
- **Productividad por funcionario**
- **Solicitudes por dependencia**
- **Índices de satisfacción ciudadana**

**Exportación de datos:**
- **Formato Excel** para análisis detallado
- **PDF** para reportes ejecutivos
- **CSV** para integración con otros sistemas

---

## Preguntas Frecuentes

### ¿Cómo priorizo una solicitud urgente?
En el panel de procesamiento, seleccione "Alta Prioridad" y agregue un comentario justificando la urgencia.

### ¿Qué hago si un ciudadano no proporcionó información completa?
Use la función "Solicitar Información" que enviará automáticamente un email al ciudadano solicitando los datos faltantes.

### ¿Puedo reasignar una solicitud a otra dependencia?
Sí, desde el panel de seguimiento puede cambiar el destinatario y agregar un comentario explicando el motivo.

### ¿Cómo genero un reporte de mi productividad?
Vaya a la sección "Reportes" y seleccione "Productividad Personal" con el rango de fechas deseado.

### ¿El sistema envía notificaciones automáticamente?
No, CIVITAS - Módulo CMIN solamente envía emails cada vez que un administrador envía un trámite.

---

## Documentación T��cnica - Vistas y API

### 6.1 Views.py - Vistas Principales del Sistema

El archivo `views.py` contiene todas las vistas principales del módulo CMIN, organizadas por funcionalidad:

#### 6.1.1 Decoradores de Seguridad

```python
def role_required(allowed_roles):
    """Decorador para verificar que el usuario tenga uno de los roles permitidos"""
```

**Roles permitidos:**
- `administrador`: Acceso completo al sistema
- `delegado`: Acceso a funciones de gestión y seguimiento
- `campo`: Acceso limitado a DesUr (redirigido automáticamente)

#### 6.1.2 Vistas de Autenticación

##### Login Unificado
- **Vista:** `login_view(request)`
- **Template:** `login.html`
- **Funcionalidad:** 
  - Autenticación unificada para usuarios CMIN y DesUr
  - Migración automática de usuarios legacy
  - Redirección inteligente según rol y permisos
  - Registro de accesos en `LoginDate`

##### Gestión de Usuarios
- **Vista:** `users_render(request)`
- **Template:** `users.html`
- **Acceso:** Solo administradores
- **Funcionalidad:** Creación de nuevos usuarios con validación de permisos

#### 6.1.3 Vistas de Gestión de Solicitudes

##### Tabla Principal de Solicitudes
- **Vista:** `tables(request)`
- **Template:** `tables.html`
- **Acceso:** Administradores y delegados
- **Datos mostrados:**
  - Solicitudes pendientes (`SolicitudesPendientes`)
  - Solicitudes enviadas (`SolicitudesEnviadas`)
  - Usuarios activos del staff
  - Opciones de prioridad

##### Envío de Correos
- **Vista:** `sendMail(request)`
- **Funcionalidad:**
  - Envío automático de solicitudes por correo
  - Adjuntar documentos PDF
  - Asignación de prioridades y usuarios
  - Manejo de errores SMTP con logging detallado
  - Creación automática de folios

##### Seguimiento de Solicitudes
- **Vista:** `seguimiento(request)`
- **Template:** `send.html`
- **Características:**
  - Sistema de filtros avanzado (fecha, estado, usuario, prioridad)
  - Subida de documentos de seguimiento
  - Estadísticas en tiempo real
  - Cierre de solicitudes con comentarios

#### 6.1.4 Funciones Auxiliares

##### Gestión de Documentos de Seguimiento
- **Función:** `seguimiento_docs(request, solicitud_id)`
- **Validaciones:**
  - Archivos PDF únicamente
  - Tamaño máximo: 5MB
  - Nomenclatura automática con timestamp

##### Manejo de Errores
- **Vista:** `custom_handler404(request, exception=None)`
- **Template:** `error404.html`

#### 6.1.5 Sistema de Excel

##### Importación de Licitaciones
- **Vista:** `subir_excel(request)`
- **Template:** `excel/upload_excel.html`
- **Columnas requeridas:**
  - Fecha límite
  - No. licitación  
  - Descripción
- **Validaciones:** Verificación de estructura y actualización automática de estados

##### Exportación de Reportes
- **Vista:** `get_excel(request)`
- **Funcionalidad:** Generación de reportes completos en Excel con múltiples hojas
- **Utilidad:** `ExcelManager` para formateo profesional

### 6.2 API Views - Servicios REST

#### 6.2.1 AgeoMobileViewSet

Viewset especializado para la aplicación móvil de encuestas:

```python
class AgeoMobileViewSet(viewsets.ViewSet):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
```

##### Endpoint: Recibir Encuesta Offline
- **Método:** POST
- **Ruta:** `/api/recibir_encuesta_offline/`
- **Permisos:** Acceso público (`AllowAny`)
- **Funcionalidad:**
  - Recepción de encuestas desde dispositivos móviles
  - Generación automática de UUID únicos
  - Validación mediante `OfflineSerializer`
  - Logging detallado para depuración

**Ejemplo de respuesta exitosa:**
```json
{
    "status": "success",
    "message": "Encuesta guardada correctamente",
    "data": {
        "id": 123,
        "uuid": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

### 6.3 Modelos de Datos (models.py)

#### 6.3.1 Sistema de Usuarios Unificado

##### Modelo Users (CustomUser)
Extiende `AbstractUser` con funcionalidades específicas del sistema:

**Campos adicionales:**
- `rol`: Rol del usuario (administrador, delegado, campo)
- `foto`: Imagen de perfil
- `area`: Área de trabajo asignada
- `telefono`: Número de contacto

**Métodos de permisos:**
- `has_cmin_access()`: Verifica acceso al módulo CMIN
- `has_desur_access()`: Verifica acceso al módulo DesUr
- `can_create_user_type()`: Valida permisos para crear usuarios
- `can_access_tables()`: Acceso a tablas de gestión
- `can_access_seguimiento()`: Acceso a seguimiento
- `can_access_admin()`: Acceso administrativo

#### 6.3.2 Modelos de Gestión

##### SolicitudesPendientes
Almacena solicitudes en proceso:
- `nomSolicitud`: Nombre identificativo
- `fechaSolicitud`: Fecha de creación
- `destinatario`: Correo electrónico destino
- `doc_FK`: Relación con documento (Files)

##### SolicitudesEnviadas  
Registro de solicitudes procesadas:
- `nomSolicitud`: Identificación de la solicitud
- `fechaEnvio`: Timestamp automático
- `user_FK`: Usuario que envió (Users)
- `doc_FK`: Documento asociado (Files)
- `prioridad`: Nivel de urgencia
- `usuario_asignado`: Responsable asignado

##### Seguimiento
Sistema de tracking de solicitudes:
- `solicitud_FK`: Solicitud relacionada
- `user_FK`: Usuario que realiza seguimiento
- `comentario`: Observaciones
- `documento`: Archivo PDF de respaldo
- `nomSeg`: Nombre del seguimiento

##### Close
Cierre formal de solicitudes:
- `solicitud_FK`: Solicitud a cerrar
- `user_FK`: Usuario que cierra
- `comentario`: Motivo de cierre
- `seguimiento_FK`: Último seguimiento (opcional)

### 6.4 Formularios (forms.py)

#### 6.4.1 Formularios de Usuario

##### UsersRender
Formulario de creación de usuarios con validaciones:
- Verificación de permisos del creador
- Validación de unicidad de email y username
- Encriptación automática de contraseñas
- Asignación de roles según permisos

##### Login
Formulario simplificado de autenticación:
- Campos: usuario y contraseña
- Validación básica de formato

##### UsersConfig  
Actualización de perfil de usuario:
- Modificación de datos personales
- Cambio de foto de perfil
- Actualización de información de contacto

#### 6.4.2 Formularios Administrativos

##### UploadExcel
Carga de archivos Excel para licitaciones:
- Validación de formato de archivo
- Verificación de estructura de columnas
- Procesamiento con pandas

### 6.5 Serializers (serializers.py)

#### 6.5.1 OfflineSerializer
Serialización para encuestas móviles:
- Validación de datos de encuesta
- Formato compatible con aplicación móvil
- Manejo de campos opcionales

#### 6.5.2 OnlineSerializer  
Para encuestas en línea (funcionalidad extendida):
- Validación en tiempo real
- Integración con formularios web

### 6.6 Utilidades del Sistema

#### 6.6.1 ExcelManager (utils/ExcelManager.py)
Clase especializada para manejo de archivos Excel:

**Características:**
- Formateo profesional con xlsxwriter
- Múltiples hojas de trabajo
- Estilos personalizados para headers
- Exportación de modelos Django a Excel
- Configuración de anchos de columna automática

**Métodos principales:**
- `create_formats()`: Define estilos de celda
- `export_model_to_sheet()`: Convierte QuerySet a hoja Excel
- `apply_formatting()`: Aplica formato profesional

#### 6.6.2 Context Processors (context_processor.py)
Procesadores de contexto para templates:
- Variables globales disponibles en todos los templates
- Información de usuario actual
- Configuraciones del sistema
- Contadores y estadísticas

### 6.7 Configuración de URLs

#### 6.7.1 URLs principales (urls.py)
Rutas del módulo CMIN con control de acceso:

```python
urlpatterns = [
    path('main/', view.master, name='master'),
    path('signin/', view.users_render, name='users'),
    path('', view.login_view, name='login'),
    path('tables/', view.tables, name='tablas'),
    path('seguimiento/', view.seguimiento, name='seguimiento'),
    path('bandeja/', view.bandeja_entrada, name='bandeja_entrada'),
    path('notificaciones/', view.notifications, name='notificaciones'),
    path('excel/', view.subir_excel, name="excel"),
    path('api/', include('portaldu.cmin.api_urls')),
]
```

#### 6.7.2 URLs de API (api_urls.py)
Endpoints REST para servicios externos:
- Integración con aplicaciones móviles
- Servicios de encuestas
- APIs de sincronización

### 6.8 Seguridad y Logging

#### 6.8.1 Sistema de Logging
Configuración detallada para seguimiento:
- Logger principal: `__name__` 
- Niveles: INFO, WARNING, ERROR
- Registro de autenticaciones
- Seguimiento de errores SMTP
- Logs de API calls

#### 6.8.2 Validaciones de Seguridad
- Decorador `@role_required()` para control de acceso
- Validación de permisos en formularios
- Sanitización de archivos subidos
- Verificación de tamaños y tipos de archivo

### 6.9 Integración con DesUr

#### 6.9.1 Modelos Compartidos
El sistema CMIN utiliza modelos del módulo DesUr:
- `Files`: Documentos del sistema
- `soli`: Solicitudes de ciudadanos  
- `data`: Información de ciudadanos

#### 6.9.2 Sincronización Automática
- Migración automática de usuarios legacy
- Sincronización de solicitudes entre módulos
- Mantenimiento de integridad referencial

---

## 7. Casos de Uso Avanzados

### 7.1 Flujo Completo de Solicitud

1. **Recepción:** Ciudadano crea solicitud en DesUr
2. **Procesamiento:** CMIN identifica y clasifica la solicitud
3. **Asignación:** Administrador asigna responsable y prioridad
4. **Envío:** Sistema envía por correo con documentos adjuntos
5. **Seguimiento:** Tracking continuo con documentos de respaldo
6. **Cierre:** Finalización formal con comentarios y archivos

### 7.2 Gestión de Licitaciones

1. **Carga:** Importación masiva desde Excel
2. **Validación:** Verificación automática de estructura
3. **Activación:** Estado automático según fechas límite
4. **Monitoreo:** Dashboard de licitaciones activas
5. **Reportes:** Exportación de datos históricos

### 7.3 Sistema de Notificaciones

1. **Bandeja de entrada:** Centralización de notificaciones
2. **Estados:** Leída/No leída con timestamps
3. **Filtros:** Por tipo, fecha, usuario
4. **Acciones:** Marcado masivo y individual

---

Esta documentación técnica proporciona una visión completa del sistema CIVITAS - CMIN, cubriendo desde la arquitectura de código hasta los casos de uso específicos. El sistema está diseñado para ser escalable, seguro y fácil de mantener, con una separación clara de responsabilidades entre módulos.

---

*Manual actualizado para la versión 2025.1 del Sistema CIVITAS - Módulo CMIN. Documento sujeto a actualizaciones conforme evolucione la plataforma.*
