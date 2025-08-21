#!/usr/bin/env python3
"""
Script de demostración para usar el endpoint de Crear Ciudadano
Este script muestra cómo interactuar con la API REST de DesUr
"""

import requests
import json
import uuid
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/ageo/api/"
USERNAME = "admin"  # Cambiar por tu usuario empleado
PASSWORD = "password123"  # Cambiar por tu contraseña

class DesUrAPIDemo:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.base_url = BASE_URL

    def authenticate(self, username, password):
        """
        Paso 1: Autenticar empleado
        """
        print("🔐 Autenticando empleado...")

        # En este ejemplo usamos autenticación básica de Django
        # En producción usarías JWT o Token Authentication
        login_url = "http://localhost:8000/ageo/auth/login/"

        # Para este demo, simularemos que ya tenemos el token
        # En la práctica obtendrías el token del endpoint de login
        self.token = "demo_token_123"

        # Configurar headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            # En producción: 'Authorization': f'Bearer {self.token}'
        })

        print("✅ Autenticación exitosa")
        return True

    def crear_session_uuid(self):
        """
        Paso 2: Crear UUID de sesión
        Esto simula la creación de una sesión de trámite
        """
        print("🆔 Creando UUID de sesión...")

        session_uuid = str(uuid.uuid4())
        print(f"✅ UUID generado: {session_uuid}")

        # En la aplicación real, este UUID se crearía en el modelo Uuid
        return session_uuid

    def crear_ciudadano_ejemplo(self, session_uuid):
        """
        Paso 3: Crear ciudadano usando el endpoint
        """
        print("👤 Creando nuevo ciudadano...")

        # URL del endpoint
        url = f"{self.base_url}ciudadanos/"

        # Datos del ciudadano
        datos_ciudadano = {
            "nombre": "MARÍA",
            "pApe": "GONZÁLEZ",
            "mApe": "LÓPEZ",
            "bDay": "1990-03-15",
            "tel": "+525551234567",
            "curp": "GOLM900315MDFNPR08",
            "sexo": "Femenino",
            "dirr": "Avenida Revolución 456, Col. Centro, CP 20000",
            "asunto": "DOP00009",  # Solicitud de pavimentación
            "disc": "sin discapacidad",
            "etnia": "No pertenece a una etnia",
            "vul": "No pertenece a un grupo vulnerable",
            "uuid_session": session_uuid
        }

        print("📤 Enviando datos al servidor...")
        print(f"URL: {url}")
        print("Datos enviados:")
        print(json.dumps(datos_ciudadano, indent=2, ensure_ascii=False))

        try:
            # Hacer la petición POST
            response = self.session.post(url, json=datos_ciudadano)

            print(f"\n📨 Respuesta del servidor:")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 201:
                ciudadano_creado = response.json()
                print("✅ Ciudadano creado exitosamente!")
                print("Datos del ciudadano creado:")
                print(json.dumps(ciudadano_creado, indent=2, ensure_ascii=False))

                return ciudadano_creado
            else:
                print(f"❌ Error al crear ciudadano:")
                print(f"Código: {response.status_code}")
                try:
                    error_data = response.json()
                    print("Detalles del error:")
                    print(json.dumps(error_data, indent=2, ensure_ascii=False))
                except:
                    print(f"Respuesta: {response.text}")
                return None

        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión. Asegúrate de que el servidor Django esté ejecutándose.")
            print("💡 Ejecuta: python manage.py runserver")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
            return None

    def consultar_ciudadano(self, ciudadano_id):
        """
        Paso 4: Consultar el ciudadano creado
        """
        print(f"\n🔍 Consultando ciudadano ID: {ciudadano_id}")

        url = f"{self.base_url}ciudadanos/{ciudadano_id}/"

        try:
            response = self.session.get(url)

            if response.status_code == 200:
                ciudadano = response.json()
                print("✅ Ciudadano encontrado:")
                print(f"Nombre completo: {ciudadano['nombre_completo']}")
                print(f"Edad: {ciudadano['edad']} años")
                print(f"CURP: {ciudadano['curp']}")
                print(f"Teléfono: {ciudadano['tel']}")
                print(f"Asunto: {ciudadano['asunto']}")

                return ciudadano
            else:
                print(f"❌ Error al consultar ciudadano: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error consultando ciudadano: {str(e)}")
            return None

    def buscar_ciudadanos(self, termino_busqueda):
        """
        Paso 5: Demostrar búsqueda de ciudadanos
        """
        print(f"\n🔎 Buscando ciudadanos con término: '{termino_busqueda}'")

        url = f"{self.base_url}ciudadanos/buscar/"
        params = {'q': termino_busqueda}

        try:
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                resultados = response.json()
                print(f"✅ Búsqueda completada:")

                if 'results' in resultados:
                    ciudadanos = resultados['results']
                    print(f"Encontrados: {len(ciudadanos)} ciudadanos")

                    for i, ciudadano in enumerate(ciudadanos[:3], 1):
                        print(f"{i}. {ciudadano['nombre_completo']} - {ciudadano['curp']}")
                else:
                    print("No se encontraron resultados")

                return resultados
            else:
                print(f"❌ Error en búsqueda: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error en búsqueda: {str(e)}")
            return None

def main():
    """
    Función principal que ejecuta la demostración completa
    """
    print("🚀 DEMOSTRACIÓN DEL ENDPOINT: Crear Ciudadano")
    print("=" * 50)

    # Inicializar cliente
    api = DesUrAPIDemo()

    # Paso 1: Autenticar
    if not api.authenticate(USERNAME, PASSWORD):
        return

    # Paso 2: Crear UUID de sesión
    session_uuid = api.crear_session_uuid()

    # Paso 3: Crear ciudadano
    ciudadano = api.crear_ciudadano_ejemplo(session_uuid)

    if ciudadano:
        ciudadano_id = ciudadano.get('data_ID')

        # Paso 4: Consultar ciudadano creado
        api.consultar_ciudadano(ciudadano_id)

        # Paso 5: Demostrar búsqueda
        api.buscar_ciudadanos("MARÍA")

    print("\n" + "=" * 50)
    print("✅ Demostración completada")

def ejemplo_con_curl():
    """
    Muestra cómo hacer la misma petición usando cURL
    """
    print("\n🔧 EJEMPLO CON cURL:")
    print("=" * 30)

    curl_command = '''
# 1. Crear ciudadano
curl -X POST http://localhost:8000/ageo/api/ciudadanos/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer tu_token" \\
  -d '{
    "nombre": "MARÍA",
    "pApe": "GONZÁLEZ",
    "mApe": "LÓPEZ",
    "bDay": "1990-03-15",
    "tel": "+525551234567",
    "curp": "GOLM900315MDFNPR08",
    "sexo": "Femenino",
    "dirr": "Avenida Revolución 456, Col. Centro",
    "asunto": "DOP00009",
    "disc": "sin discapacidad",
    "etnia": "No pertenece a una etnia",
    "vul": "No pertenece a un grupo vulnerable",
    "uuid_session": "12345678-1234-5678-9abc-123456789def"
  }'

# 2. Consultar ciudadano por ID
curl -X GET http://localhost:8000/ageo/api/ciudadanos/123/ \\
  -H "Authorization: Bearer tu_token"

# 3. Buscar ciudadanos
curl -X GET "http://localhost:8000/ageo/api/ciudadanos/buscar/?q=MARÍA" \\
  -H "Authorization: Bearer tu_token"

# 4. Listar con filtros
curl -X GET "http://localhost:8000/ageo/api/ciudadanos/?nombre=MARÍA&page=1" \\
  -H "Authorization: Bearer tu_token"
'''

    print(curl_command)

if __name__ == "__main__":
    print("Selecciona una opción:")
    print("1. Ejecutar demostración completa")
    print("2. Mostrar ejemplos con cURL")

    opcion = input("\nOpción (1 o 2): ").strip()

    if opcion == "1":
        main()
    elif opcion == "2":
        ejemplo_con_curl()
    else:
        print("Opción no válida")
