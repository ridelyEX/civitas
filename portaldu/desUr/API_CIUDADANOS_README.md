# API REST para CRUD de Ciudadanos - DesUr

Esta documentación describe los endpoints disponibles para manipular los datos de ciudadanos en el sistema DesUr.

## 🔐 Autenticación

Todos los endpoints requieren autenticación. Incluir el token en las cabeceras:
```
Authorization: Bearer <token>
```

## 📍 Endpoints Disponibles

### **CRUD Básico**

#### 1. **Crear Ciudadano**
```http
POST /api/ciudadanos/
```

**Body:**
```json
{
  "nombre": "JUAN",
  "pApe": "PÉREZ", 
  "mApe": "GARCÍA",
  "bDay": "1985-05-15",
  "tel": "+525551234567",
  "curp": "PEGJ850515HDFRRN09",
  "sexo": "Masculino",
  "dirr": "Calle Principal 123, Col. Centro",
  "asunto": "DOP00001",
  "disc": "sin discapacidad",
  "etnia": "No pertenece a una etnia", 
  "vul": "No pertenece a un grupo vulnerable",
  "uuid_session": "12345678-1234-5678-9abc-123456789def"
}
```

**Respuesta:**
```json
{
  "data_ID": 123,
  "fuuid": {
    "prime": 1,
    "uuid": "12345678-1234-5678-9abc-123456789def"
  },
  "nombre": "JUAN",
  "pApe": "PÉREZ",
  "mApe": "GARCÍA",
  "nombre_completo": "JUAN PÉREZ GARCÍA",
  "edad": 39,
  "bDay": "1985-05-15",
  "tel": "+525551234567",
  "curp": "PEGJ850515HDFRRN09",
  "sexo": "Masculino",
  "dirr": "Calle Principal 123, Col. Centro",
  "asunto": "DOP00001",
  "disc": "sin discapacidad",
  "etnia": "No pertenece a una etnia",
  "vul": "No pertenece a un grupo vulnerable"
}
```

#### 2. **Obtener Ciudadano por ID**
```http
GET /api/ciudadanos/{id}/
```

#### 3. **Actualizar Ciudadano Completo**
```http
PUT /api/ciudadanos/{id}/
```

#### 4. **Actualizar Campos Específicos**
```http
PATCH /api/ciudadanos/{id}/
```

**Body (ejemplo):**
```json
{
  "tel": "+525559876543",
  "dirr": "Nueva dirección"
}
```

#### 5. **Eliminar Ciudadano**
```http
DELETE /api/ciudadanos/{id}/
```

### **Consultas Especiales**

#### 6. **Listar Ciudadanos con Paginación**
```http
GET /api/ciudadanos/?page=1&page_size=20
```

**Filtros disponibles:**
- `nombre`: Buscar por nombre, apellido paterno o materno
- `curp`: Filtrar por CURP exacta
- `uuid`: Filtrar por UUID de sesión
- `asunto`: Filtrar por tipo de trámite
- `telefono`: Filtrar por teléfono

**Ejemplo:**
```http
GET /api/ciudadanos/?page=1&page_size=10&nombre=Juan&asunto=DOP00001
```

#### 7. **Búsqueda Avanzada**
```http
GET /api/ciudadanos/buscar/?q=Juan
```

Busca en nombre, apellidos, CURP, teléfono y dirección.

#### 8. **Obtener por UUID de Sesión**
```http
GET /api/ciudadanos/uuid/{uuid}/
```

#### 9. **Obtener por CURP**
```http
GET /api/ciudadanos/curp/{curp}/
```

#### 10. **Validar CURP**
```http
POST /api/ciudadanos/validar-curp/
```

**Body:**
```json
{
  "curp": "PEGJ850515HDFRRN09"
}
```

**Respuesta:**
```json
{
  "curp": "PEGJ850515HDFRRN09",
  "existe": true,
  "disponible": false
}
```

### **Datos Relacionados**

#### 11. **Obtener Solicitudes del Ciudadano**
```http
GET /api/ciudadanos/{id}/solicitudes/
```

#### 12. **Obtener Documentos del Ciudadano**
```http
GET /api/ciudadanos/{id}/documentos/
```

#### 13. **Estadísticas de Ciudadanos**
```http
GET /api/ciudadanos/estadisticas/
```

**Respuesta:**
```json
{
  "total_ciudadanos": 1250,
  "por_genero": {
    "Masculino": 650,
    "Femenino": 600
  },
  "por_asunto": [
    {"asunto": "DOP00001", "count": 300},
    {"asunto": "DOP00002", "count": 250}
  ],
  "registros_recientes": 10
}
```

## 📝 Validaciones

### Campos Obligatorios:
- `nombre`: Mínimo 1 carácter
- `pApe`: Apellido paterno
- `mApe`: Apellido materno
- `bDay`: Fecha de nacimiento (no puede ser futura)
- `curp`: Formato válido de 18 caracteres
- `uuid_session`: UUID válido existente

### Formato CURP:
```
^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$
```

### Campos Únicos:
- `curp`: No puede repetirse entre ciudadanos

## 🚨 Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 201 | Creado exitosamente |
| 204 | Eliminado exitosamente |
| 400 | Datos inválidos |
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | No encontrado |
| 500 | Error interno |

## 📊 Ejemplos de Respuestas de Error

**Validación fallida:**
```json
{
  "curp": ["Ya existe un ciudadano con esta CURP"],
  "bDay": ["La fecha de nacimiento no puede ser futura"]
}
```

**CURP inválida:**
```json
{
  "curp": ["CURP debe tener el formato correcto (18 caracteres)"]
}
```

**UUID de sesión inválido:**
```json
{
  "uuid_session": ["UUID de sesión no válido"]
}
```

## 🔧 Uso con JavaScript/Fetch

```javascript
// Crear ciudadano
const crearCiudadano = async (datos) => {
  const response = await fetch('/api/ciudadanos/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(datos)
  });
  
  return await response.json();
};

// Buscar ciudadanos
const buscarCiudadanos = async (query) => {
  const response = await fetch(`/api/ciudadanos/buscar/?q=${encodeURIComponent(query)}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

## 🔧 Uso con Python/Requests

```python
import requests

# Configuración
base_url = "http://localhost:8000/ageo/api/"
headers = {"Authorization": f"Bearer {token}"}

# Crear ciudadano
datos = {
    "nombre": "JUAN",
    "pApe": "PÉREZ",
    # ... otros campos
}

response = requests.post(
    f"{base_url}ciudadanos/", 
    json=datos, 
    headers=headers
)

if response.status_code == 201:
    ciudadano = response.json()
    print(f"Ciudadano creado: {ciudadano['data_ID']}")
```

## 📚 Modelos de Datos

### Ciudadano (data)
```python
{
  "data_ID": int,           # ID único
  "fuuid": Uuid,           # UUID de sesión
  "nombre": str,           # Nombre
  "pApe": str,             # Apellido paterno
  "mApe": str,             # Apellido materno
  "bDay": date,            # Fecha nacimiento
  "asunto": str,           # Tipo de trámite
  "tel": str,              # Teléfono
  "curp": str,             # CURP
  "sexo": str,             # Género
  "dirr": str,             # Dirección
  "disc": str,             # Discapacidad
  "etnia": str,            # Etnia
  "vul": str,              # Vulnerabilidad
  "edad": int,             # Calculado
  "nombre_completo": str   # Calculado
}
```
