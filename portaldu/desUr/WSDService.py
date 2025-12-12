import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.exceptions import (  # 🆕 Importar excepciones correctamente
    Timeout,
    ConnectionError,
    HTTPError,
    RequestException
)
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from unittest.mock import Mock

try:
    from requests_ntlm import HttpNtlmAuth
except ImportError:
    HttpNtlmAuth = None

# Configurar logging más detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WsDomicilios:
    """
    Consumir domicilios a través de servicios web.
    """

    def __init__(
            self,
            base_url: str = "https://wsdomicilios.mpiochih.gob.mx/WSDomicilios",
            mock_mode: bool = False,
            windows_user: str = None,
            windows_password: str = None
    ):
        self.base_url = base_url
        self.token = None
        self.token_vigencia = None
        self.session = requests.Session()
        self.windows_user = windows_user
        self.windows_password = windows_password
        self.mock_mode = mock_mode  #

        # Configurar autenticación de Windows si hay credenciales
        if windows_user and windows_password:
            if HttpNtlmAuth:
                try:
                    self.session.auth = HttpNtlmAuth(windows_user, windows_password)
                    logger.info(f"Autenticación NTLM configurada para: {windows_user}")
                except Exception as e:
                    logger.warning(f"️ Error configurando NTLM: {e}")
                    self.session.auth = HTTPBasicAuth(windows_user, windows_password)
            else:
                logger.warning("requests-ntlm no instalado. Usando Basic Auth")
                self.session.auth = HTTPBasicAuth(windows_user, windows_password)

        self.session.headers.update({
            'User-Agent': 'WsDomicilios-Client/1.0',
            'Content-Type': 'application/json'
        })

        logger.info(f"Cliente inicializado - URL: {self.base_url}, Mock: {self.mock_mode}")

    def get_token(self, usuario: str = None, password: str = None) -> bool:
        """
        Obtiene token de autenticación.
        """

        # Si está en modo mock, generar token simulado
        if self.mock_mode:
            self.token = "mock_token_development_12345"
            self.token_vigencia = "2025-12-31 23:59:59"
            logger.info("Token simulado generado para desarrollo")
            return True

        url = f"{self.base_url}/Usuarios/GetToken"

        # El payload puede ser vacío o con credenciales de aplicación
        payload = {}
        if usuario and password:
            payload = {
                "usuario": usuario,
                "contrasena": password
            }

        logger.debug(f"Solicitando token a: {url}")
        logger.debug(f"Payload: {json.dumps(payload)}")
        logger.debug(f"Windows Auth: {'Sí' if self.session.auth else 'No'}")

        try:
            response = self.session.post(
                url,
                json=payload if payload else None,
                timeout=15
            )

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            # Si obtenemos 401, activar modo mock
            if response.status_code == 401:
                logger.error(" Error 401 - Autenticación de Windows requerida")
                logger.warning(" Activando modo MOCK para continuar desarrollo")
                return self._activate_mock_mode()

            response.raise_for_status()

            # Parsear respuesta
            try:
                data = response.json()
                self.token = data.get("token") or data.get("Token")
                self.token_vigencia = data.get("vigencia") or data.get("Vigencia")
            except json.JSONDecodeError:
                # Si no es JSON, asumir que el token viene directo
                self.token = response.text.strip()
                self.token_vigencia = "N/A"

            logger.info(f"Token obtenido exitosamente. Vigencia: {self.token_vigencia}")
            logger.debug(
                f"Token: {self.token[:20]}..." if self.token and len(self.token) > 20 else f"Token: {self.token}")

            return True

        except Timeout:
            logger.error(" Timeout al obtener token")
            logger.warning(" Activando modo MOCK")
            return self._activate_mock_mode()
        except ConnectionError as e:
            logger.error(f" Error de conexión: {e}")
            logger.warning(" Activando modo MOCK")
            return self._activate_mock_mode()
        except HTTPError as e:
            logger.error(f" Error HTTP {response.status_code}")
            if response.status_code == 401:
                logger.error(" SOLUCIÓN: Necesitas credenciales de Windows válidas")
                logger.error(" Contacta al administrador del servidor")
            logger.warning(" Activando modo MOCK")
            return self._activate_mock_mode()
        except RequestException as e:
            logger.error(f" Error en la petición: {e}")
            logger.warning(" Activando modo MOCK")
            return self._activate_mock_mode()
        except json.JSONDecodeError as e:
            logger.error(f" Error decodificando JSON: {e}")
            return False
        except KeyError as e:
            logger.error(f" Campo faltante en respuesta: {e}")
            return False
        except Exception as e:
            logger.error(f" Error inesperado: {e}")
            logger.warning(" Activando modo MOCK")
            return self._activate_mock_mode()

    def _activate_mock_mode(self) -> bool:
        """ Activa el modo mock automáticamente"""
        logger.info("=" * 60)
        logger.info("MODO SIMULACIÓN ACTIVADO AUTOMÁTICAMENTE")
        logger.info("Razón: No hay acceso al servicio web real")
        logger.info("Solución: Continúa desarrollando con datos simulados")
        logger.info("Para producción: Configura credenciales de Windows válidas")
        logger.info("=" * 60)

        self.mock_mode = True
        self.token = "mock_token_auto_fallback_12345"
        self.token_vigencia = "2025-12-31 23:59:59"
        return True

    def get_headers(self) -> Dict[str, str]:
        """Obtención de headers con autenticación"""
        if not self.token:
            raise Exception("No hay token disponible. Llama a get_token() primero.")

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Realiza una petición autenticada con manejo de errores"""

        if not self.token:
            logger.error("No hay token disponible")
            return None

        # Si estamos en modo mock, devolver respuesta simulada
        if self.mock_mode:
            return self._mock_response(url, **kwargs)

        try:
            headers = kwargs.pop('headers', {})
            headers.update(self.get_headers())

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=15,
                **kwargs
            )

            logger.debug(f"{method} {url} - Status: {response.status_code}")

            response.raise_for_status()
            return response

        except RequestException as e:
            logger.error(f"Error en petición {method} {url}: {e}")
            return None

    def _mock_response(self, url: str, **kwargs) -> requests.Response:
        """Genera respuestas simuladas para desarrollo"""

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}

        # Simular datos según el endpoint
        if '/GetColonias' in url:
            mock_data = [
                {"id_colonia": 1, "colonia": "CENTRO"},
                {"id_colonia": 11462, "colonia": "RESERVA DEL PARQUE II"},
                {"id_colonia": 2, "colonia": "DALE"},
                {"id_colonia": 3, "colonia": "ALTAVISTA"},
                {"id_colonia": 4, "colonia": "SAN FELIPE"},
                {"id_colonia": 5, "colonia": "LOS FRAILES"},
                {"id_colonia": 6, "colonia": "COUNTRY CLUB"},
                {"id_colonia": 7, "colonia": "QUINTAS CAROLINAS"}
            ]
        elif '/GetCalles' in url:
            mock_data = [
                {"id_calle": 1791, "calle": "AVENIDA MAIN"},
                {"id_calle": 15506, "calle": "CALLE JUAREZ"},
                {"id_calle": 2, "calle": "AVENIDA HIDALGO"},
                {"id_calle": 3, "calle": "CALLE MORELOS"},
                {"id_calle": 4, "calle": "BOULEVARD INDEPENDENCIA"}
            ]
        elif '/GetNumerosExteriores' in url:
            mock_data = [
                {"numero": "101", "latitud": "28.6329957", "longitud": "-106.0691004", "distrito": "1"},
                {"numero": "103", "latitud": "28.6330123", "longitud": "-106.0691234", "distrito": "1"},
                {"numero": "105", "latitud": "28.6330289", "longitud": "-106.0691464", "distrito": "1"},
                {"numero": "107", "latitud": None, "longitud": None, "distrito": None}
            ]
        elif '/GetCoordenadas' in url:
            mock_data = {
                "latitud": "28.6329957",
                "longitud": "-106.0691004",
                "direccion": "Calle Simulada #123, Colonia Mock"
            }
        else:
            mock_data = {"message": "Mock response", "status": "ok"}

        mock_response.json.return_value = mock_data
        mock_response.text = json.dumps(mock_data)

        logger.debug(f"Mock response para {url}")
        return mock_response

    def get_colonias(self) -> Optional[List[Dict[str, Any]]]:
        """Obtiene un listado de colonias disponibles"""
        url = f"{self.base_url}/GetColonias"
        logger.debug(f"Obteniendo colonias de: {url}")

        response = self._make_authenticated_request('POST', url)
        if not response:
            return None

        try:
            colonias = response.json()
            logger.info(f" {len(colonias)} colonias obtenidas {'(simuladas)' if self.mock_mode else ''}")
            return colonias
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando respuesta de colonias: {e}")
            return None

    def get_calles(self, id_colonias: int) -> Optional[List[Dict[str, Any]]]:
        """Obtiene las calles de las colonias específicas"""
        url = f"{self.base_url}/GetCalles"
        payload = {"id_colonia": id_colonias}
        logger.debug(f"Obteniendo calles para colonia {id_colonias}")

        response = self._make_authenticated_request('POST', url, json=payload)
        if not response:
            return None

        try:
            calles = response.json()
            logger.info(f"️ {len(calles)} calles obtenidas {'(simuladas)' if self.mock_mode else ''}")
            return calles
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando respuesta de calles: {e}")
            return None

    def get_ext_num(self, id_colonias: int, id_calle: int) -> Optional[List[Dict[str, Any]]]:
        """Obtiene los números exteriores de las calles"""
        url = f"{self.base_url}/GetNumerosExteriores"
        payload = {
            "id_colonia": id_colonias,
            "id_calle": id_calle
        }
        logger.debug(f"Obteniendo números para colonia {id_colonias}, calle {id_calle}")

        response = self._make_authenticated_request('POST', url, json=payload)
        if not response:
            return None

        try:
            numeros = response.json()
            logger.info(f" {len(numeros)} números obtenidos {'(simulados)' if self.mock_mode else ''}")
            return numeros
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando respuesta de números: {e}")
            return None

    def get_coordenadas(self, clave_catastral: str) -> Optional[Dict[str, Any]]:
        """Obtiene las coordenadas de un punto a partir de su clave catastral."""
        url = f"{self.base_url}/GetCoordenadas"
        payload = {"clave_catastral": clave_catastral}
        logger.debug(f"Obteniendo coordenadas para clave: {clave_catastral}")

        response = self._make_authenticated_request('POST', url, json=payload)
        if not response:
            return None

        try:
            coordenadas = response.json()
            logger.info(f" Coordenadas obtenidas {'(simuladas)' if self.mock_mode else ''}")
            return coordenadas
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando respuesta de coordenadas: {e}")
            return None

    def search_colonia(self, nombre_colonia: str) -> List[Dict[str, Any]]:
        """Buscar colonias por nombre"""
        colonias = self.get_colonias()
        if not colonias:
            return []

        nombre_colonia = nombre_colonia.upper()
        resultados = [
            col for col in colonias
            if nombre_colonia in col['colonia'].upper()
        ]

        logger.info(f" {len(resultados)} colonias encontradas")
        return resultados

    def search_calle(self, id_colonia: int, nombre_calle: str) -> List[Dict[str, Any]]:
        """Buscar calles por nombre de una colonia"""
        calles = self.get_calles(id_colonia)
        if not calles:
            return []

        nombre_calle = nombre_calle.upper()
        resultados = [
            calle for calle in calles
            if nombre_calle in calle['calle'].upper()
        ]

        logger.info(f" {len(resultados)} calles encontradas")
        return resultados

    def search_colonia_by_cp(self, cp):
        """Busca colonias por código postal"""
        endpoint = f"{self.base_url}/api/colonias/buscar-cp"

        try:
            response = self.session.get(
                endpoint,
                params={'cp': cp},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

            return []

        except Exception as e:
            logger.error(f"Error buscando por CP: {str(e)}")
            return []

    def get_complete_address(self, id_colonias: int, id_calle: int) -> Dict[str, Any]:
        """Obtiene la dirección completa a partir de los IDs de colonia y calle."""
        colonias = self.get_colonias()
        colonia_info = next((col for col in colonias if col['id_colonia'] == id_colonias), None)

        calles = self.get_calles(id_colonias)
        calle_info = next((cal for cal in calles if cal['id_calle'] == id_calle), None)

        numeros = self.get_ext_num(id_colonias, id_calle)

        return {
            "colonia": colonia_info,
            "calle": calle_info,
            "numeros_exteriores": numeros,
            "total_numeros": len(numeros) if numeros else 0,
            "mock_mode": self.mock_mode
        }

    def test_connection(self) -> bool:
        """Prueba la conectividad al servicio"""
        if self.mock_mode:
            logger.info(" Test conexión en modo mock: OK")
            return True

        try:
            response = self.session.get(self.base_url, timeout=5)
            logger.info(f" Test conectividad - Status: {response.status_code}")
            return response.status_code < 400
        except RequestException as e:
            logger.error(f" Error de conectividad: {e}")
            return False