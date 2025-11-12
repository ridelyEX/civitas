import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class WSDConfig:
    """Configuración del servicio WS Domicilios"""
    BASE_URL: str = os.getenv('WSD_BASE_URL', 'http://10.218.2.253/WSDomicilios')
    WINDOWS_USER: Optional[str] = os.getenv('WSD_WINDOWS_USER')
    WINDOWS_PASSWORD: Optional[str] = os.getenv('WSD_WINDOWS_PASSWORD')
    APP_USER: Optional[str] = os.getenv('WSD_APP_USER')
    APP_PASSWORD: Optional[str] = os.getenv('WSD_APP_PASSWORD')
    MOCK_MODE: bool = os.getenv('WSD_MOCK_MODE', 'false').lower() == 'true'
    TIMEOUT: int = int(os.getenv('WSD_TIMEOUT', '15'))
    MAX_RETRIES: int = int(os.getenv('WSD_MAX_RETRIES', '3'))