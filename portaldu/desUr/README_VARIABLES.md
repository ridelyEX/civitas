# Documentación de Variables - Aplicación desUr

## Descripción General
La aplicación **desUr** (Desarrollo Urbano) es un módulo del portal de trámites que permite a los ciudadanos realizar solicitudes relacionadas con obras públicas, mantenimiento urbano y servicios municipales.

---

## 📊 Variables de Modelos (models.py)

### Modelo: Uuid
Maneja identificadores únicos para las sesiones de usuario.

| Variable | Tipo | Descripción | Constraints |
|----------|------|-------------|-------------|
| `prime` | AutoField | Clave primaria | Primary Key |
| `uuid` | UUIDField | Identificador único universal | Default: uuid.uuid4, No editable |

### Modelo: data
Almacena los datos personales del solicitante.

| Variable | Tipo | Descripción | Constraints |
|----------|------|-------------|-------------|
| `data_ID` | AutoField | Clave primaria | Primary Key |
| `fuuid` | ForeignKey | Referencia a Uuid | On delete: CASCADE |
| `nombre` | CharField | Nombre del solicitante | Max length: 30 |
| `pApe` | CharField | Apellido paterno | Max length: 30 |
| `mApe` | CharField | Apellido materno | Max length: 30 |
| `bDay` | DateField | Fecha de nacimiento | - |
| `asunto` | CharField | Código del trámite solicitado | Max length: 30 |
| `tel` | PhoneNumberField | Número telefónico | Región: MX |
| `curp` | CharField | CURP del solicitante | Max length: 18 |
| `sexo` | CharField | Género del solicitante | Max length: 10 |
| `dirr` | TextField | Dirección completa | - |
| `disc` | CharField | Tipo de discapacidad | Max length: 30, Default: "sin discapacidad" |
| `etnia` | CharField | Grupo étnico | Max length: 30, Default: "sin etnia" |

### Modelo: SubirDocs
Maneja la carga de documentos adjuntos.

| Variable | Tipo | Descripción | Constraints |
|----------|------|-------------|-------------|
| `doc_ID` | AutoField | Clave primaria | Primary Key |
| `fuuid` | ForeignKey | Referencia a Uuid | On delete: CASCADE |
| `nomDoc` | CharField | Nombre del documento | Max length: 50, Nullable |
| `descDoc` | CharField | Descripción del documento | Max length: 100 |
| `doc` | FileField | Archivo cargado | Upload to: 'documents/' |
| `fechaDoc` | DateTimeField | Fecha de carga | Auto now add, Nullable |

### Modelo: Pagos
Registra información de pagos realizados.

| Variable | Tipo | Descripción | Constraints |
|----------|------|-------------|-------------|
| `pago_ID` | AutoField | Clave primaria | Primary Key |
| `data_ID` | ForeignKey | Referencia a data | On delete: CASCADE |
| `fecha` | DateTimeField | Fecha del pago | Nullable |
| `pfm` | CharField | Forma de pago | Max length: 80, Nullable |

### Modelo: soli
Almacena las solicitudes de trámites.

| Variable | Tipo | Descripción | Constraints |
|----------|------|-------------|-------------|
| `soli_ID` | AutoField | Clave primaria | Primary Key |
| `data_ID` | ForeignKey | Referencia a data | On delete: CASCADE |
| `doc_ID` | ForeignKey | Referencia a SubirDocs | On delete: CASCADE, Nullable |
| `dirr` | TextField | Dirección del problema/solicitud | - |
| `calle` | CharField | Nombre de la calle | Max length: 50, Nullable |
| `colonia` | CharField | Nombre de la colonia | Max length: 50, Nullable |
| `cp` | CharField | Código postal | Max length: 5, Nullable |
| `descc` | TextField | Descripción detallada | Nullable |
| `fecha` | DateTimeField | Fecha de la solicitud | Auto now add, Nullable |
| `info` | TextField | Información adicional | Nullable |
| `puo` | CharField | Punto de origen/ubicación | Max length: 50, Nullable |
| `folio` | CharField | Folio generado | - |
| `foto` | ImageField | Foto del problema | Upload to: 'fotos/' |

---

## 🎯 Variables de Vistas (views.py)

### Vista: base
| Variable | Tipo | Descripción |
|----------|------|-------------|
| `uuid` | str | UUID obtenido de cookies |

### Vista: home
| Variable | Tipo | Descripción |
|----------|------|-------------|
| `uuidM` | str | UUID del usuario (cookie o generado) |
| `new` | Uuid | Nueva instancia de Uuid |

### Vista: intData
| Variable | Tipo | Descripción |
|----------|------|-------------|
| `direccion` | str | Dirección obtenida de GET |
| `uuid` | str | UUID de cookies |
| `uid` | Uuid | Objeto Uuid |
| `asunto` | str | Código del trámite |
| `nombre` | str | Nombre del solicitante |
| `pApe` | str | Apellido paterno |
| `mApe` | str | Apellido materno |
| `bDay` | str | Fecha de nacimiento |
| `tel` | str | Número telefónico |
| `curp` | str | CURP |
| `sexo` | str | Género |
| `dirr` | str | Dirección |
| `etnia` | str | Grupo étnico |
| `disc` | str | Tipo de discapacidad |
| `datos` | data | Instancia del modelo data |
| `context` | dict | Contexto para template |

### Vista: soliData
| Variable | Tipo | Descripción |
|----------|------|-------------|
| `uuid` | str | UUID de cookies |
| `is_mobile` | bool | Detecta dispositivo móvil |
| `is_tablet` | bool | Detecta tablet |
| `is_pc` | bool | Detecta PC |
| `solicitud` | soli | Instancia de solicitud |
| `uid` | Uuid | Objeto Uuid |
| `direccion` | str | Dirección |
| `asunto` | str | Código del trámite |
| `dp` | data | Datos personales |
| `id_dp` | int | ID de datos personales |
| `dirr` | str | Dirección del problema |
| `calle` | str | Calle parseada |
| `colonia` | str | Colonia parseada |
| `cp` | str | Código postal parseado |
| `descc` | str | Descripción |
| `info` | str | Información adicional |
| `puo` | str | Punto de origen |
| `img` | File | Archivo de imagen |
| `imgpath` | str | Ruta de imagen |
| `name` | str | Nombre del archivo |
| `file_keys` | list | Claves de archivos temporales |
| `file` | File | Archivo individual |
| `desc` | str | Descripción del documento |
| `documento` | SubirDocs | Instancia de documento |
| `puo_texto` | str | Texto del punto de origen |
| `folio` | str | Folio generado |
| `solicitudes` | QuerySet | Lista de solicitudes |

### Vista: doc
| Variable | Tipo | Descripción |
|----------|------|-------------|
| `uuid` | str | UUID de cookies |
| `datos` | data | Datos del usuario |
| `asunto` | str | Código del trámite |
| `action` | str | Acción del formulario |

---

## 🌐 Variables de Templates HTML

### Códigos de Trámites (di.html)
| Código | Descripción |
|--------|-------------|
| `DOP00001` | Arreglo de calles de terracería |
| `DOP00002` | Bacheo de calles |
| `DOP00003` | Limpieza de arroyos al sur de la ciudad |
| `DOP00004` | Limpieza o mantenimiento de rejillas pluviales |
| `DOP00005` | Pago de costo de participación en licitaciones de obra pública |
| `DOP00006` | Rehabilitación de calles |
| `DOP00007` | Retiro de escombro y material de arrastre |
| `DOP00008` | Solicitud de material caliche |
| `DOP00009` | Solicitud de pavimentación de calles |
| `DOP00010` | Solicitud de reductores de velocidad |
| `DOP00011` | Solicitud de pintura para señalamientos viales |
| `DOP00012` | Arreglo de derrumbe de bardas |
| `DOP00013` | Tapeado |

### Variables de Contexto en Templates
| Variable | Tipo | Descripción | Templates |
|----------|------|-------------|-----------|
| `uuid` | str | Identificador de sesión | Todos |
| `asunto` | str | Código del trámite | di.html, ds.html, dg.html |
| `dir` | str | Dirección | di.html, ds.html |
| `google_key` | str | API Key de Google Maps | di.html, ds.html |
| `datos` | object | Datos del usuario | dg.html |
| `soli` | list | Lista de solicitudes | ds.html |
| `is_mobile` | bool | Tipo de dispositivo | ds.html |
| `is_tablet` | bool | Tipo de dispositivo | ds.html |
| `is_pc` | bool | Tipo de dispositivo | ds.html |
| `puo` | str | Punto de origen | ds.html |
| `imgpath` | str | Ruta de imagen | ds.html |

### Variables de Formularios HTML
| Campo | Name | Type | Descripción |
|-------|------|------|-------------|
| Nombre | `nombre` | text | Nombre del solicitante |
| Apellido Paterno | `pApe` | text | Apellido paterno |
| Apellido Materno | `mApe` | text | Apellido materno |
| Fecha de Nacimiento | `bDay` | date | Fecha de nacimiento |
| Teléfono | `tel` | tel | Número telefónico |
| CURP | `curp` | text | CURP |
| Sexo | `sexo` | select | Género |
| Dirección | `dir` | textarea | Dirección completa |
| Etnia | `etnia` | select | Grupo étnico |
| Discapacidad | `discapacidad` | select | Tipo de discapacidad |
| Asunto | `asunto` | select | Código del trámite |
| Descripción | `descc` | textarea | Descripción del problema |
| Información | `info` | textarea | Información adicional |
| Punto de Origen | `puo` | text | Ubicación específica |
| Imagen | `src` | file | Foto del problema |
| Archivo | `tempfile_*` | file | Documentos adjuntos |
| Descripción Doc | `tempdesc_*` | text | Descripción del documento |
| Acción | `action` | hidden | Acción del formulario |

---

## 📜 Variables de Archivos JavaScript

### btnScripts.js
Variables relacionadas con botones y acciones:
- `btnGuardar` - Botón de guardar
- `btnDescargar` - Botón de descarga
- `btnEnviar` - Botón de envío
- `btnWhatsApp` - Botón de WhatsApp

### fotos.js
Variables para manejo de fotografías:
- `fotoInput` - Input de archivo de foto
- `previewImg` - Imagen de previsualización
- `canvas` - Canvas para edición
- `ctx` - Contexto del canvas
- `photoData` - Datos de la foto

### loader.js
Variables para indicadores de carga:
- `loader` - Elemento loader
- `showLoader()` - Función mostrar loader
- `hideLoader()` - Función ocultar loader

### modals.js
Variables para ventanas modales:
- `modal` - Elemento modal
- `openModal()` - Función abrir modal
- `closeModal()` - Función cerrar modal
- `modalContent` - Contenido del modal

### mPhoto.js
Variables para fotos en dispositivos móviles:
- `mPhotoInput` - Input móvil para fotos
- `camera` - Acceso a cámara
- `stream` - Stream de video

---

## 🔧 Variables de Configuración

### Settings Variables
| Variable | Descripción |
|----------|-------------|
| `GOOGLE_API_KEY` | Clave API de Google Maps |
| `MEDIA_URL` | URL base para archivos media |
| `MEDIA_ROOT` | Directorio raíz para archivos media |

### URL Variables
Variables utilizadas en urls.py:
- `urlpatterns` - Lista de patrones de URL
- `path` - Función de path de Django
- `include` - Función include de Django

---

## 🎨 Variables de Estilos CSS

### Clases CSS Principales
- `.form` - Contenedor de formulario
- `.text` - Estilo de texto
- `.right` - Contenedor derecho
- `.left` - Contenedor izquierdo
- `.btn` - Botones
- `.modal` - Ventanas modales
- `.loader` - Indicador de carga

---

## 📱 Variables de Sesión

### Session Variables
| Variable | Descripción |
|----------|-------------|
| `asunto` | Código del trámite en sesión |
| `puo` | Punto de origen en sesión |

### Cookie Variables
| Variable | Descripción |
|----------|-------------|
| `uuid` | Identificador único de sesión |

---

## 🔍 Variables de Validación

### Funciones de Validación
- `cut_direction()` - Parsea dirección en calle, colonia, CP
- `gen_folio()` - Genera folio único
- `wasap_msg()` - Envía mensaje por WhatsApp

---

## 📊 Estados y Tipos de Datos

### Tipos de Dispositivo
- `is_mobile` - Dispositivo móvil
- `is_tablet` - Tablet
- `is_pc` - Computadora

### Tipos de Archivo
- Documentos: PDF, DOC, DOCX
- Imágenes: JPG, PNG, GIF
- Videos: MP4, AVI (en carpeta videos)

---

## 🚀 Variables de Flujo de Proceso

1. **Inicio**: `uuid` → Generación o recuperación
2. **Datos**: `data` → Captura de información personal
3. **Solicitud**: `soli` → Creación de solicitud específica
4. **Documentos**: `SubirDocs` → Carga de archivos
5. **Finalización**: `folio` → Generación de folio único

Este README proporciona una documentación completa de todas las variables utilizadas en la aplicación desUr, organizadas por contexto y funcionalidad para facilitar el mantenimiento y desarrollo futuro.
