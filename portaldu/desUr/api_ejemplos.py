"""
Ejemplos de uso de la API REST para CRUD de Ciudadanos
Este archivo muestra cómo consumir los endpoints desde una aplicación cliente
"""

import requests
import json
from datetime import datetime

# Configuración base
API_BASE_URL = "http://localhost:8000/ageo/api/"  # Ajusta según tu configuración
AUTH_TOKEN = None  # Se obtiene después del login

class CiudadanoAPIClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'

    def login(self, username, password):
        """Autenticar empleado y obtener token"""
        url = f"{self.base_url}auth/login/"
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            self.headers['Authorization'] = f'Bearer {token}'
            return token
        return None

    # === CRUD BÁSICO ===

    def crear_ciudadano(self, datos_ciudadano, uuid_session):
        """
        Crear nuevo ciudadano
        POST /api/ciudadanos/
        """
        url = f"{self.base_url}ciudadanos/"
        datos_ciudadano['uuid_session'] = uuid_session

        response = requests.post(url, json=datos_ciudadano, headers=self.headers)
        return response.json(), response.status_code

    def obtener_ciudadano(self, ciudadano_id):
        """
        Obtener ciudadano por ID
        GET /api/ciudadanos/{id}/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

    def actualizar_ciudadano(self, ciudadano_id, datos_actualizados):
        """
        Actualizar ciudadano completo
        PUT /api/ciudadanos/{id}/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/"
        response = requests.put(url, json=datos_actualizados, headers=self.headers)
        return response.json(), response.status_code

    def actualizar_ciudadano_parcial(self, ciudadano_id, campos_actualizados):
        """
        Actualizar campos específicos del ciudadano
        PATCH /api/ciudadanos/{id}/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/"
        response = requests.patch(url, json=campos_actualizados, headers=self.headers)
        return response.json(), response.status_code

    def eliminar_ciudadano(self, ciudadano_id):
        """
        Eliminar ciudadano
        DELETE /api/ciudadanos/{id}/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/"
        response = requests.delete(url, headers=self.headers)
        return response.status_code == 204

    # === CONSULTAS ESPECIALES ===

    def listar_ciudadanos(self, page=1, page_size=20, filtros=None):
        """
        Listar ciudadanos con paginación y filtros
        GET /api/ciudadanos/?page=1&page_size=20&nombre=Juan&curp=ABC123
        """
        url = f"{self.base_url}ciudadanos/"
        params = {'page': page, 'page_size': page_size}

        if filtros:
            params.update(filtros)

        response = requests.get(url, params=params, headers=self.headers)
        return response.json(), response.status_code

    def buscar_ciudadanos(self, query):
        """
        Búsqueda avanzada de ciudadanos
        GET /api/ciudadanos/buscar/?q=Juan
        """
        url = f"{self.base_url}ciudadanos/buscar/"
        params = {'q': query}
        response = requests.get(url, params=params, headers=self.headers)
        return response.json(), response.status_code

    def obtener_por_uuid(self, uuid):
        """
        Obtener ciudadano por UUID de sesión
        GET /api/ciudadanos/uuid/{uuid}/
        """
        url = f"{self.base_url}ciudadanos/uuid/{uuid}/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

    def obtener_por_curp(self, curp):
        """
        Obtener ciudadano por CURP
        GET /api/ciudadanos/curp/{curp}/
        """
        url = f"{self.base_url}ciudadanos/curp/{curp}/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

    def validar_curp(self, curp):
        """
        Validar si CURP ya existe
        POST /api/ciudadanos/validar-curp/
        """
        url = f"{self.base_url}ciudadanos/validar-curp/"
        data = {'curp': curp}
        response = requests.post(url, json=data, headers=self.headers)
        return response.json(), response.status_code

    def obtener_solicitudes_ciudadano(self, ciudadano_id):
        """
        Obtener solicitudes de un ciudadano
        GET /api/ciudadanos/{id}/solicitudes/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/solicitudes/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

    def obtener_documentos_ciudadano(self, ciudadano_id):
        """
        Obtener documentos de un ciudadano
        GET /api/ciudadanos/{id}/documentos/
        """
        url = f"{self.base_url}ciudadanos/{ciudadano_id}/documentos/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

    def obtener_estadisticas(self):
        """
        Obtener estadísticas de ciudadanos
        GET /api/ciudadanos/estadisticas/
        """
        url = f"{self.base_url}ciudadanos/estadisticas/"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code

# === EJEMPLOS DE USO ===

def ejemplos_uso():
    """Ejemplos prácticos de cómo usar la API"""

    # Inicializar cliente
    client = CiudadanoAPIClient(API_BASE_URL)

    # 1. Autenticar empleado
    token = client.login("usuario_empleado", "password123")
    if not token:
        print("Error en autenticación")
        return

    # 2. Crear nuevo ciudadano
    nuevo_ciudadano = {
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
        "vul": "No pertenece a un grupo vulnerable"
    }

    uuid_session = "12345678-1234-5678-9abc-123456789def"
    resultado, status = client.crear_ciudadano(nuevo_ciudadano, uuid_session)

    if status == 201:
        print("✅ Ciudadano creado exitosamente")
        ciudadano_id = resultado['data_ID']
        print(f"ID del ciudadano: {ciudadano_id}")

        # 3. Obtener el ciudadano creado
        ciudadano, status = client.obtener_ciudadano(ciudadano_id)
        if status == 200:
            print(f"✅ Ciudadano obtenido: {ciudadano['nombre_completo']}")
            print(f"Edad: {ciudadano['edad']} años")

        # 4. Actualizar teléfono del ciudadano
        actualizar_datos = {"tel": "+525559876543"}
        resultado, status = client.actualizar_ciudadano_parcial(ciudadano_id, actualizar_datos)
        if status == 200:
            print("✅ Teléfono actualizado")

        # 5. Obtener solicitudes del ciudadano
        solicitudes, status = client.obtener_solicitudes_ciudadano(ciudadano_id)
        if status == 200:
            print(f"✅ Solicitudes encontradas: {len(solicitudes)}")
    else:
        print(f"❌ Error creando ciudadano: {resultado}")

    # 6. Buscar ciudadanos
    resultados, status = client.buscar_ciudadanos("JUAN")
    if status == 200:
        print(f"✅ Búsqueda completada: {len(resultados.get('results', []))} resultados")

    # 7. Validar CURP
    validacion, status = client.validar_curp("PEGJ850515HDFRRN09")
    if status == 200:
        print(f"✅ CURP validada - Existe: {validacion['existe']}")

    # 8. Obtener estadísticas
    stats, status = client.obtener_estadisticas()
    if status == 200:
        print(f"✅ Total de ciudadanos: {stats['total_ciudadanos']}")
        print(f"Por género: {stats['por_genero']}")

if __name__ == "__main__":
    ejemplos_uso()
