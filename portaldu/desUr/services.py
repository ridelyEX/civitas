import requests
import logging
import urllib.parse
import re

logger = logging.getLogger(__name__)

class LocalGISService:
    """Servicio para usar ArcGIS Server local"""

    BASE_URL = "https://sigmunchih.mpiochih.gob.mx/server/rest/services"
    GEOCODE_URL = f"{BASE_URL}/Composite_Locator/GeocodeServer"

    # Agregar la configuración de servicios
    SERVICES = {
        'arcgis_server': {
            'name': 'ArcGIS Server Chihuahua',
            'url': 'https://sigmunchih.mpiochih.gob.mx/server/rest/services',
            'geocode_url': f'{BASE_URL}/Composite_Locator/GeocodeServer',
            'enabled': True,
            'priority': 1
        },
        'openstreetmap': {
            'name': 'OpenStreetMap Nominatim',
            'url': 'https://nominatim.openstreetmap.org',
            'enabled': True,
            'priority': 2
        }
    }

    @staticmethod
    def get_service_status():
        """Verificar el estado de los servicios de geocodificación"""
        status = {}

        # Verificar ArcGIS Server
        try:
            response = requests.get(f"{LocalGISService.BASE_URL}?f=json", timeout=5, verify=False)
            status['arcgis_server'] = {
                'available': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
        except:
            status['arcgis_server'] = {
                'available': False,
                'response_time': None
            }

        # Verificar OpenStreetMap
        try:
            response = requests.get("https://nominatim.openstreetmap.org/status", timeout=5)
            status['openstreetmap'] = {
                'available': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
        except:
            status['openstreetmap'] = {
                'available': False,
                'response_time': None
            }

        return status

    @staticmethod
    def _clean_address(address):
        """Limpia y normaliza la dirección"""
        if not address:
            return ""

        # Convertir a minúsculas y limpiar espacios
        clean = address.strip().lower()

        # Normalizar abreviaciones comunes
        replacements = {
            'av.': 'avenida',
            'ave.': 'avenida',
            'c.': 'calle',
            'col.': 'colonia',
            'fracc.': 'fraccionamiento',
            'priv.': 'privada',
            'blvd.': 'boulevard',
            'prol.': 'prolongación',
            'calz.': 'calzada',
            'carr.': 'carretera',
            'no.': 'número',
            'núm.': 'número',
            '#': 'número'
        }

        for abbrev, full in replacements.items():
            clean = clean.replace(abbrev, full)

        # Limpiar espacios múltiples
        clean = ' '.join(clean.split())

        return clean

    @staticmethod
    def _is_postal_code(address):
        """Detecta si la dirección es principalmente un código postal"""
        # Código postal mexicano: 5 dígitos
        postal_pattern = r'^\s*\d{5}\s*$'
        return bool(re.match(postal_pattern, address.strip()))

    @staticmethod
    def _has_street_number(address):
        """Detecta si la dirección tiene número exterior"""
        # Buscar patrones como "Calle 123", "Av Universidad 456", etc.
        number_patterns = [
            r'\d+',  # Cualquier número
            r'número\s+\d+',  # "número 123"
            r'no\s+\d+',  # "no 123"
            r'#\s*\d+',  # "#123"
        ]

        for pattern in number_patterns:
            if re.search(pattern, address.lower()):
                return True
        return False

    @staticmethod
    def _extract_street_name(address):
        """Extrae solo el nombre de la calle, sin número"""
        # Remover números y palabras relacionadas
        clean = address.lower()

        # Patrones para remover
        patterns_to_remove = [
            r'\bnúmero\s+\d+\b',
            r'\bno\.?\s+\d+\b',
            r'\b#\s*\d+\b',
            r'\b\d+\b',  # Cualquier número suelto
        ]

        for pattern in patterns_to_remove:
            clean = re.sub(pattern, '', clean)

        # Limpiar espacios múltiples
        clean = ' '.join(clean.split())

        return clean.strip()

    @staticmethod
    def _geocode_with_number(address):
        """Geocodifica direcciones con número exterior"""
        try:
            # Primero intentar la dirección completa
            result = LocalGISService._try_arcgis_geocode(f"{address}, Chihuahua")
            if result:
                return result

            # Si no funciona, intentar sin "número" pero con el dígito
            clean = address.replace('número', '').replace('no.', '').replace('no ', '')
            result = LocalGISService._try_arcgis_geocode(f"{clean}, Chihuahua")
            if result:
                return result

            return None

        except Exception as e:
            logger.error(f"Error geocodificando dirección con número: {str(e)}")
            return None

    @staticmethod
    def _try_arcgis_geocode(address, timeout=5):
        """Intenta geocodificar con ArcGIS Server con timeout optimizado"""
        try:
            url = f"{LocalGISService.GEOCODE_URL}/findAddressCandidates"

            # Limpiar y preparar la dirección
            clean_address = ' '.join(address.split())

            params = {
                'SingleLine': clean_address,
                'f': 'json',
                'outFields': 'AddNum,StName,StType,City,Postal,Nbrhd',  # Solo campos necesarios
                'maxLocations': 3,  # Reducir para mejor performance
                'outSR': '4326',
                'searchExtent': '-106.5,-106.0,28.0,29.0',
            }

            logger.info(f"Geocodificando con ArcGIS (timeout={timeout}s): {clean_address}")

            response = requests.get(
                url,
                params=params,
                timeout=timeout,
                verify=False,
                headers={
                    'User-Agent': 'DesUr-LocalGIS/1.0',
                    'Accept': 'application/json',
                    'Connection': 'close'  # Evitar conexiones persistentes
                }
            )

            if response.status_code != 200:
                logger.warning(f"ArcGIS respondió con código {response.status_code}")
                return None

            data = response.json()

            if 'error' in data:
                logger.warning(f"Error en respuesta ArcGIS: {data['error']}")
                return None

            if 'candidates' in data and len(data['candidates']) > 0:
                best_candidate = max(data['candidates'], key=lambda x: x.get('score', 0))

                if best_candidate.get('score', 0) > 40 and 'location' in best_candidate:
                    location = best_candidate['location']
                    attrs = best_candidate.get('attributes', {})

                    components = LocalGISService._extract_address_components(attrs, best_candidate.get('address', ''))

                    result = {
                        'address': best_candidate.get('address', '') or f"{clean_address}, Chihuahua",
                        'lat': location['y'],
                        'lng': location['x'],
                        'score': best_candidate.get('score', 0),
                        'source': 'ArcGIS',
                        'components': components
                    }

                    logger.info(f"Resultado ArcGIS exitoso: score={result['score']}")
                    return result

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout ArcGIS después de {timeout}s - Fallback a OSM")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Error de conexión ArcGIS - Fallback a OSM")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en ArcGIS: {str(e)}")
            return None

    @staticmethod
    def geocode_address(address):
        """Geocodifica con estrategia optimizada y fallbacks rápidos"""
        try:
            clean_address = LocalGISService._clean_address(address)
            logger.info(f"Geocodificando: {address} -> {clean_address}")

            # **Estrategia 1: Código postal directo (más rápido)**
            if LocalGISService._is_postal_code(clean_address):
                logger.info("Detectado código postal")
                result = LocalGISService._geocode_postal_code(clean_address)
                if result:
                    return result

            # **Estrategia 2: Direcciones residenciales específicas**
            if LocalGISService._detect_residential_address(clean_address):
                logger.info("Detectada dirección residencial")
                result = LocalGISService._geocode_house_number_fast(clean_address)
                if result:
                    return result

            # **Estrategia 3: ArcGIS con timeout corto (solo 1 intento)**
            result = LocalGISService._try_arcgis_geocode(clean_address, timeout=3)
            if result:
                return result

            # **Estrategia 4: Fallback inmediato a OpenStreetMap**
            logger.info("Fallback a OpenStreetMap")
            return LocalGISService._geocode_with_osm_fast(address)

        except Exception as e:
            logger.error(f"Error en geocodificación: {str(e)}")
            return LocalGISService._geocode_with_osm_fast(address)

    @staticmethod
    def _geocode_house_number_fast(address):
        """Geocodificación rápida para números de casa"""
        try:
            components = LocalGISService._parse_address_components(address)

            if not components['number'] or not components['street']:
                return None

            # Solo las variantes más efectivas
            search_variants = [
                f"{components['street']} {components['number']}, Chihuahua",
                f"{components['number']} {components['street']}, Chihuahua",
            ]

            # Solo 1 intento con ArcGIS (timeout muy corto)
            for variant in search_variants:
                result = LocalGISService._try_arcgis_geocode(variant, timeout=2)
                if result:
                    return result

            # Fallback inmediato a OSM
            return LocalGISService._geocode_with_osm_fast(f"{components['street']} {components['number']}, Chihuahua, México")

        except Exception as e:
            logger.error(f"Error geocodificando casa: {str(e)}")
            return None

    @staticmethod
    def _geocode_with_osm_fast(address):
        """OpenStreetMap optimizado con timeouts cortos"""
        try:
            search_queries = [
                f"{address}, Chihuahua, Chihuahua, México",
                f"{address}, Chihuahua, México"
            ]

            for query in search_queries:
                try:
                    url = "https://nominatim.openstreetmap.org/search"
                    params = {
                        'q': query,
                        'format': 'json',
                        'limit': 3,
                        'addressdetails': 1,
                        'countrycodes': 'mx',
                        'bounded': 1,
                        'viewbox': '-106.5,28.0,-106.0,29.0'
                    }

                    headers = {
                        'User-Agent': 'DesUr/1.0',
                        'Accept': 'application/json'
                    }

                    logger.info(f"Geocodificando con OSM: {query}")

                    response = requests.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=5  # Timeout corto
                    )

                    if response.status_code != 200:
                        continue

                    data = response.json()

                    if data and len(data) > 0:
                        best = data[0]

                        # Extraer componentes de OSM
                        address_parts = best.get('address', {})
                        components = {
                            'calle': address_parts.get('road', ''),
                            'numero': address_parts.get('house_number', ''),
                            'colonia': address_parts.get('neighbourhood', address_parts.get('suburb', '')),
                            'codigo_postal': address_parts.get('postcode', ''),
                            'ciudad': address_parts.get('city', 'Chihuahua'),
                            'estado': address_parts.get('state', 'Chihuahua'),
                            'full_address': best.get('display_name', query)
                        }

                        result = {
                            'address': best.get('display_name', query),
                            'lat': float(best['lat']),
                            'lng': float(best['lon']),
                            'score': 80,  # Score fijo para OSM
                            'source': 'OpenStreetMap',
                            'components': components
                        }

                        logger.info(f"Resultado OSM exitoso: {result['address']}")
                        return result

                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout OSM para: {query}")
                    continue
                except Exception as e:
                    logger.warning(f"Error OSM para {query}: {str(e)}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error en OSM fallback: {str(e)}")
            return None

    @staticmethod
    def _geocode_postal_code(postal_code):
        """Geocodificación específica para códigos postales"""
        try:
            # Códigos postales conocidos de Chihuahua
            postal_coords = {
                '31000': {'lat': 28.6353, 'lng': -106.0889, 'name': 'Centro'},
                '31200': {'lat': 28.6500, 'lng': -106.1000, 'name': 'San Felipe'},
                '31203': {'lat': 28.6400, 'lng': -106.1100, 'name': 'Bosques del Pedregal'},
                '31204': {'lat': 28.6450, 'lng': -106.1150, 'name': 'Quintas del Sol'},
                '31210': {'lat': 28.6300, 'lng': -106.0800, 'name': 'Residencial Campestre'},
            }

            if postal_code in postal_coords:
                coord = postal_coords[postal_code]

                components = {
                    'calle': '',
                    'numero': '',
                    'colonia': coord['name'],
                    'codigo_postal': postal_code,
                    'ciudad': 'Chihuahua',
                    'estado': 'Chihuahua',
                    'full_address': f"CP {postal_code}, {coord['name']}, Chihuahua"
                }

                return {
                    'address': f"Código Postal {postal_code}, {coord['name']}, Chihuahua",
                    'lat': coord['lat'],
                    'lng': coord['lng'],
                    'score': 95,
                    'source': 'LocalDB',
                    'components': components
                }

            # Si no está en la base local, intentar con OSM
            return LocalGISService._geocode_with_osm_fast(f"CP {postal_code}, Chihuahua, México")

        except Exception as e:
            logger.error(f"Error geocodificando CP: {str(e)}")
            return None

    @staticmethod
    def _extract_address_components(attributes, full_address):
        """Extrae componentes estructurados de la respuesta de ArcGIS"""
        components = {
            'calle': '',
            'numero': '',
            'colonia': '',
            'codigo_postal': '',
            'ciudad': 'Chihuahua',
            'estado': 'Chihuahua',
            'full_address': full_address
        }

        try:
            # Extraer número
            if attributes.get('AddNum'):
                components['numero'] = str(attributes['AddNum']).strip()

            # Extraer calle
            street_parts = []
            if attributes.get('StPreDir'):  # Dirección previa (Norte, Sur, etc.)
                street_parts.append(attributes['StPreDir'])
            if attributes.get('StPreType'):  # Tipo previo (Av, Calle, etc.)
                street_parts.append(attributes['StPreType'])
            if attributes.get('StName'):  # Nombre de la calle
                street_parts.append(attributes['StName'])
            if attributes.get('StType'):  # Tipo posterior (Calle, Avenida, etc.)
                street_parts.append(attributes['StType'])
            if attributes.get('StDir'):  # Dirección posterior
                street_parts.append(attributes['StDir'])

            if street_parts:
                components['calle'] = ' '.join(street_parts).strip()
            elif attributes.get('PlaceName'):
                components['calle'] = attributes['PlaceName']

            # Extraer colonia/vecindario
            if attributes.get('Nbrhd'):
                components['colonia'] = attributes['Nbrhd']
            elif attributes.get('District'):
                components['colonia'] = attributes['District']

            # Extraer código postal
            if attributes.get('Postal'):
                components['codigo_postal'] = str(attributes['Postal']).strip()

            # Extraer ciudad
            if attributes.get('City'):
                components['ciudad'] = attributes['City']

            # Si no se extrajo calle del attributes, intentar del full_address
            if not components['calle'] and full_address:
                components = LocalGISService._parse_address_from_text(full_address, components)

            # Construir dirección completa formateada
            full_parts = []
            if components['calle']:
                if components['numero']:
                    full_parts.append(f"{components['calle']} {components['numero']}")
                else:
                    full_parts.append(components['calle'])

            if components['colonia']:
                full_parts.append(components['colonia'])

            if components['ciudad']:
                full_parts.append(components['ciudad'])

            if components['codigo_postal']:
                full_parts.append(f"CP {components['codigo_postal']}")

            components['full_address'] = ', '.join(full_parts) if full_parts else full_address

            logger.info(f"Componentes extraídos: {components}")
            return components

        except Exception as e:
            logger.error(f"Error extrayendo componentes: {str(e)}")
            components['full_address'] = full_address
            return components

    @staticmethod
    def _parse_address_from_text(address_text, existing_components):
        """Extrae componentes adicionales del texto de dirección"""
        try:
            # Limpiar el texto
            clean_text = address_text.lower().strip()

            # Extraer número si no se tiene
            if not existing_components['numero']:
                number_match = re.search(r'\b(\d+)\b', clean_text)
                if number_match:
                    existing_components['numero'] = number_match.group(1)

            # Extraer código postal
            if not existing_components['codigo_postal']:
                cp_patterns = [
                    r'\bcp\s*(\d{5})\b',
                    r'\b(\d{5})\b'
                ]
                for pattern in cp_patterns:
                    cp_match = re.search(pattern, clean_text)
                    if cp_match:
                        existing_components['codigo_postal'] = cp_match.group(1)
                        break

            # Extraer colonia
            if not existing_components['colonia']:
                colonia_patterns = [
                    r'(?:colonia|col\.?|fraccionamiento|fracc\.?|residencial)\s+([^,]+)',
                    r'(?:quintas|villas|jardines|bosques|lomas)\s+([^,]+)'
                ]
                for pattern in colonia_patterns:
                    colonia_match = re.search(pattern, clean_text)
                    if colonia_match:
                        existing_components['colonia'] = colonia_match.group(1).strip().title()
                        break

            # Extraer calle si no se tiene
            if not existing_components['calle']:
                # Remover número, colonia y código postal para obtener la calle
                street_text = clean_text

                # Remover código postal
                street_text = re.sub(r'\bcp\s*\d{5}\b', '', street_text)
                street_text = re.sub(r'\b\d{5}\b', '', street_text)

                # Remover colonia
                for pattern in [r'(?:colonia|col\.?|fraccionamiento|fracc\.?|residencial)\s+[^,]+',
                              r'(?:quintas|villas|jardines|bosques|lomas)\s+[^,]+']:
                    street_text = re.sub(pattern, '', street_text)

                # Remover ciudad
                street_text = re.sub(r'\bchihuahua\b', '', street_text)

                # Remover comas y espacios extra
                street_text = re.sub(r'[,]+', ' ', street_text)
                street_text = ' '.join(street_text.split())

                if street_text and len(street_text) > 2:
                    existing_components['calle'] = street_text.title()

            return existing_components

        except Exception as e:
            logger.error(f"Error parseando dirección desde texto: {str(e)}")
            return existing_components

    @staticmethod
    def _geocode_with_osm(address):
        """Fallback usando OpenStreetMap que también devuelve componentes"""
        try:
            search_queries = [
                f"{address}, Chihuahua, Chihuahua, México",
                f"{address}, Chihuahua, México",
                f"{address}, México"
            ]

            for query in search_queries:
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': 5,
                    'bounded': 1,
                    'viewbox': '-106.5,28.0,-106.0,29.0'  # Bounding box para Chihuahua
                }

                headers = {'User-Agent': 'DesUr/1.0'}

                logger.info(f"Geocodificando con OSM: {query}")

                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()

                if data and len(data) > 0:
                    result = data[0]  # Tomar el primer resultado

                    # Extraer componentes de OSM
                    osm_address = result.get('address', {})
                    components = {
                        'calle': '',
                        'numero': '',
                        'colonia': '',
                        'codigo_postal': '',
                        'ciudad': 'Chihuahua',
                        'estado': 'Chihuahua',
                        'full_address': result.get('display_name', '')
                    }

                    # Extraer número y calle
                    if osm_address.get('house_number') and osm_address.get('road'):
                        components['numero'] = osm_address['house_number']
                        components['calle'] = osm_address['road']
                    elif osm_address.get('road'):
                        components['calle'] = osm_address['road']

                    # Extraer colonia
                    if osm_address.get('neighbourhood'):
                        components['colonia'] = osm_address['neighbourhood']
                    elif osm_address.get('suburb'):
                        components['colonia'] = osm_address['suburb']
                    elif osm_address.get('quarter'):
                        components['colonia'] = osm_address['quarter']

                    # Extraer código postal
                    if osm_address.get('postcode'):
                        components['codigo_postal'] = osm_address['postcode']

                    # Extraer ciudad
                    if osm_address.get('city'):
                        components['ciudad'] = osm_address['city']
                    elif osm_address.get('town'):
                        components['ciudad'] = osm_address['town']

                    # Construir dirección formateada
                    full_parts = []
                    if components['calle']:
                        if components['numero']:
                            full_parts.append(f"{components['calle']} {components['numero']}")
                        else:
                            full_parts.append(components['calle'])

                    if components['colonia']:
                        full_parts.append(components['colonia'])

                    if components['ciudad']:
                        full_parts.append(components['ciudad'])

                    if components['codigo_postal']:
                        full_parts.append(f"CP {components['codigo_postal']}")

                    if full_parts:
                        components['full_address'] = ', '.join(full_parts)

                    return {
                        'lat': float(result['lat']),
                        'lng': float(result['lon']),
                        'address': components['full_address'],
                        'score': 85,  # Score fijo para OSM
                        'components': components
                    }

            return None

        except Exception as e:
            logger.error(f"Error geocodificando con OSM: {str(e)}")
            return None

    @staticmethod
    def _detect_residential_address(address):
        """Detecta si es una dirección residencial específica"""
        residential_keywords = [
            'casa', 'num', 'número', '#', 'fraccionamiento', 'fracc',
            'residencial', 'privada', 'quintas', 'villas', 'jardines',
            'bosques', 'lomas', 'cerrada', 'andador', 'retorno'
        ]

        address_lower = address.lower()

        # Debe tener un número Y una palabra clave residencial
        has_number = bool(re.search(r'\d+', address_lower))
        has_residential_keyword = any(keyword in address_lower for keyword in residential_keywords)

        return has_number and (has_residential_keyword or len(address.split()) >= 3)

    @staticmethod
    def _enhanced_street_search(address):
        """Búsqueda mejorada para calles en fraccionamientos"""
        try:
            # Extraer componentes de la dirección
            components = LocalGISService._parse_address_components(address)

            if not components:
                return None

            # Generar múltiples variantes de búsqueda
            search_variants = []

            if components['number'] and components['street']:
                search_variants.extend([
                    f"{components['street']} {components['number']}",
                    f"{components['number']} {components['street']}",
                    f"Calle {components['street']} {components['number']}",
                    f"Avenida {components['street']} {components['number']}",
                ])

            if components['neighborhood']:
                for variant in search_variants[:2]:  # Solo las primeras 2
                    search_variants.append(f"{variant}, {components['neighborhood']}")

            # Agregar contexto de Chihuahua a todas las variantes
            chihuahua_variants = []
            for variant in search_variants:
                chihuahua_variants.extend([
                    f"{variant}, Chihuahua",
                    f"{variant}, Chihuahua, Chihuahua",
                    f"{variant}, Chihuahua, México"
                ])

            # Intentar geocodificar cada variante
            for variant in chihuahua_variants:
                result = LocalGISService._try_arcgis_geocode(variant)
                if result:
                    logger.info(f"Encontrado con variante: {variant}")
                    return result

            return None

        except Exception as e:
            logger.error(f"Error en búsqueda mejorada de calle: {str(e)}")
            return None

    @staticmethod
    def _parse_address_components(address):
        """Extrae componentes de una dirección residencial mejorado"""
        try:
            components = {
                'number': None,
                'street': None,
                'neighborhood': None,
                'original': address
            }

            address_clean = address.lower().strip()

            # Limpiar caracteres especiales y normalizar
            address_clean = re.sub(r'[^\w\s]', ' ', address_clean)
            address_clean = ' '.join(address_clean.split())

            logger.info(f"Dirección limpia para parseo: {address_clean}")

            # Patrones más específicos para números de casa
            number_patterns = [
                r'casa\s+(\d{1,4})\b',  # "casa 123" (máximo 4 dígitos)
                r'num(?:ero)?\s+(\d{1,4})\b',  # "num 123" o "numero 123"
                r'#\s*(\d{1,4})\b',  # "#123"
                r'^(\d{1,4})\s+(?!cp|codigo)',  # Número al inicio pero no CP
                r'\s(\d{1,4})\s*$',  # Número al final
            ]

            # Buscar número de casa
            for pattern in number_patterns:
                match = re.search(pattern, address_clean)
                if match:
                    potential_number = match.group(1)
                    # Validar que no sea código postal (5 dígitos)
                    if len(potential_number) <= 4:
                        components['number'] = potential_number
                        # Remover el número encontrado para limpiar la calle
                        address_clean = re.sub(pattern, ' ', address_clean)
                        break

            # Limpiar la dirección después de extraer el número
            address_clean = ' '.join(address_clean.split())

            # Detectar colonia/fraccionamiento
            neighborhood_patterns = [
                r'(?:fraccionamiento|fracc\.?)\s+([^,\d]+)',
                r'(?:residencial|privada)\s+([^,\d]+)',
                r'(?:quintas|villas|jardines|bosques|lomas)\s+([^,\d]+)',
                r'(?:colonia|col\.?)\s+([^,\d]+)',
            ]

            for pattern in neighborhood_patterns:
                match = re.search(pattern, address_clean)
                if match:
                    components['neighborhood'] = match.group(1).strip()
                    # Remover la colonia del texto para obtener la calle
                    address_clean = re.sub(pattern, '', address_clean)
                    break

            # Lo que queda debe ser la calle
            street_clean = address_clean.strip()

            # Remover palabras comunes que no son parte del nombre
            stop_words = [
                'calle', 'avenida', 'av', 'c', 'de', 'la', 'del', 'los', 'las',
                'casa', 'numero', 'num', 'chihuahua', 'cp', 'codigo'
            ]

            street_words = []
            for word in street_clean.split():
                if word not in stop_words and len(word) > 1:
                    street_words.append(word)

            if street_words:
                components['street'] = ' '.join(street_words).title()

            logger.info(f"Componentes parseados: número={components['number']}, calle={components['street']}, colonia={components['neighborhood']}")

            return components

        except Exception as e:
            logger.error(f"Error parseando componentes de dirección: {str(e)}")
            return {
                'number': None,
                'street': None,
                'neighborhood': None,
                'original': address
            }

    @staticmethod
    def reverse_geocode(lat, lng):
        """Geocodificación inversa: coordenadas → dirección"""
        try:
            logger.info(f"Geocodificación inversa para: {lat}, {lng}")

            # Intentar con ArcGIS primero
            result = LocalGISService._try_arcgis_reverse_geocode(lat, lng)
            if result:
                return result

            # Fallback a OpenStreetMap
            return LocalGISService._reverse_geocode_with_osm(lat, lng)

        except Exception as e:
            logger.error(f"Error en geocodificación inversa: {str(e)}")
            return None

    @staticmethod
    def _try_arcgis_reverse_geocode(lat, lng, timeout=5):
        """Geocodificación inversa con ArcGIS"""
        try:
            url = f"{LocalGISService.GEOCODE_URL}/reverseGeocode"

            params = {
                'location': f"{lng},{lat}",  # ArcGIS usa lng,lat
                'f': 'json',
                'outSR': '4326',
                'returnIntersection': 'false'
            }

            logger.info(f"Geocodificación inversa ArcGIS: {lat}, {lng}")

            response = requests.get(
                url,
                params=params,
                timeout=timeout,
                verify=False,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; LocalGIS/1.0)'}
            )

            if response.status_code != 200:
                logger.warning(f"ArcGIS reverse geocode respondió con código {response.status_code}")
                return None

            data = response.json()

            if 'error' in data:
                logger.warning(f"Error en respuesta ArcGIS reverse: {data['error']}")
                return None

            if 'address' in data:
                address_info = data['address']

                # Construir dirección legible
                address_parts = []
                if address_info.get('AddNum'):
                    address_parts.append(address_info['AddNum'])
                if address_info.get('StName'):
                    address_parts.append(address_info['StName'])
                if address_info.get('StType'):
                    address_parts.append(address_info['StType'])

                street_address = ' '.join(address_parts) if address_parts else 'Dirección no disponible'

                full_address = f"{street_address}, {address_info.get('City', 'Chihuahua')}, {address_info.get('Region', 'Chihuahua')}"

                components = {
                    'calle': f"{address_info.get('StName', '')} {address_info.get('StType', '')}".strip(),
                    'numero': address_info.get('AddNum', ''),
                    'colonia': address_info.get('Nbrhd', ''),
                    'ciudad': address_info.get('City', 'Chihuahua'),
                    'estado': address_info.get('Region', 'Chihuahua'),
                    'codigo_postal': address_info.get('Postal', ''),
                    'full_address': full_address
                }

                result = {
                    'address': full_address,
                    'lat': lat,
                    'lng': lng,
                    'source': 'ArcGIS Reverse',
                    'components': components
                }

                logger.info(f"Resultado ArcGIS reverse exitoso: {result['address']}")
                return result

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout en ArcGIS reverse geocode después de {timeout}s")
            return None
        except Exception as e:
            logger.error(f"Error en ArcGIS reverse geocode: {str(e)}")
            return None

    @staticmethod
    def _reverse_geocode_with_osm(lat, lng):
        """Geocodificación inversa con OpenStreetMap Nominatim"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"

            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 18,
                'accept-language': 'es'
            }

            logger.info(f"Geocodificación inversa OSM: {lat}, {lng}")

            response = requests.get(
                url,
                params=params,
                timeout=3,
                headers={'User-Agent': 'LocalGIS/1.0 (compatible)'}
            )

            if response.status_code != 200:
                logger.warning(f"OSM reverse geocode respondió con código {response.status_code}")
                return None

            data = response.json()

            if 'display_name' in data:
                address_details = data.get('address', {})

                components = {
                    'calle': address_details.get('road', ''),
                    'numero': address_details.get('house_number', ''),
                    'colonia': address_details.get('neighbourhood', address_details.get('suburb', '')),
                    'ciudad': address_details.get('city', address_details.get('town', 'Chihuahua')),
                    'estado': address_details.get('state', 'Chihuahua'),
                    'codigo_postal': address_details.get('postcode', ''),
                    'full_address': data['display_name']
                }

                result = {
                    'address': data['display_name'],
                    'lat': lat,
                    'lng': lng,
                    'source': 'OpenStreetMap',
                    'components': components
                }

                logger.info(f"Resultado OSM reverse exitoso: {result['address']}")
                return result

            return None

        except Exception as e:
            logger.error(f"Error en OSM reverse geocode: {str(e)}")
            return None

    @staticmethod
    def validate_address(address):
        """Valida que la dirección tenga el formato correcto"""
        try:
            if not address or not isinstance(address, str):
                return False, "Dirección no válida"

            address = address.strip()

            if len(address) < 3:
                return False, "La dirección debe tener al menos 3 caracteres"

            if len(address) > 200:
                return False, "La dirección es demasiado larga"

            # Verificar que no contenga solo números (podría ser coordenadas)
            if address.replace('.', '').replace(',', '').replace(' ', '').replace('-', '').isdigit():
                return False, "Formato de dirección no válido"

            # Verificar caracteres válidos
            valid_pattern = r'^[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ0-9\s\.,#\-\/]+$'
            if not re.match(valid_pattern, address):
                return False, "La dirección contiene caracteres no válidos"

            return True, "Dirección válida"

        except Exception as e:
            logger.error(f"Error validando dirección: {str(e)}")
            return False, f"Error en validación: {str(e)}"