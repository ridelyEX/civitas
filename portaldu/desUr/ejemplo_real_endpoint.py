"""
EJEMPLO REAL: Cómo usar el endpoint Crear Ciudadano
Este ejemplo muestra el uso práctico con autenticación real
"""

import requests
import json

def ejemplo_real_crear_ciudadano():
    """
    Ejemplo práctico de cómo usar el endpoint en un sistema real
    """

    # Paso 1: Configurar la petición
    url = "http://localhost:8000/ageo/api/ciudadanos/"

    # Paso 2: Preparar los datos del ciudadano
    datos_ciudadano = {
        "nombre": "CARLOS",
        "pApe": "MENDOZA",
        "mApe": "RIVERA",
        "bDay": "1985-12-10",
        "tel": "+525559876543",
        "curp": "MERC851210HDFNVR03",
        "sexo": "Masculino",
        "dirr": "Calle Morelos 789, Col. Jardines",
        "asunto": "DOP00001",  # Arreglo de calles de terracería
        "disc": "sin discapacidad",
        "etnia": "No pertenece a una etnia",
        "vul": "No pertenece a un grupo vulnerable",
        "uuid_session": "550e8400-e29b-41d4-a716-446655440000"  # UUID de sesión válido
    }

    # Paso 3: Configurar headers con autenticación
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer tu_token_aqui",  # Token obtenido del login
        # O usar autenticación de sesión Django:
        # "X-CSRFToken": "csrf_token_aqui"
    }

    # Paso 4: Hacer la petición
    try:
        response = requests.post(url, json=datos_ciudadano, headers=headers)

        if response.status_code == 201:
            # Éxito - ciudadano creado
            ciudadano = response.json()
            print("✅ Ciudadano creado exitosamente!")
            print(f"ID: {ciudadano['data_ID']}")
            print(f"Nombre: {ciudadano['nombre_completo']}")
            print(f"Edad: {ciudadano['edad']} años")
            return ciudadano

        elif response.status_code == 400:
            # Error de validación
            errores = response.json()
            print("❌ Errores de validación:")
            for campo, mensajes in errores.items():
                print(f"  {campo}: {mensajes}")

        elif response.status_code == 403:
            print("❌ Error de autenticación - verifica tu token")

        else:
            print(f"❌ Error inesperado: {response.status_code}")
            print(response.text)

    except requests.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("💡 Asegúrate de ejecutar: python manage.py runserver")

if __name__ == "__main__":
    ejemplo_real_crear_ciudadano()
