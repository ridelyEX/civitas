#!/usr/bin/env python
"""
Script de pruebas para PWA de DesUr
Verifica todas las funcionalidades implementadas
"""

import os
import json
import requests
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civitas.settings')
django.setup()

class PWATestSuite:
    def __init__(self):
        self.client = Client()
        self.base_url = "http://127.0.0.1:8000"
        self.results = []

    def log_result(self, test_name, status, message=""):
        result = {
            'test': test_name,
            'status': status,
            'message': message
        }
        self.results.append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {message}")

    def test_manifest_available(self):
        """Verificar que el manifest.json está disponible"""
        try:
            response = self.client.get('/desur/manifest.json')
            if response.status_code == 200:
                manifest_data = json.loads(response.content)
                required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
                missing_fields = [field for field in required_fields if field not in manifest_data]

                if not missing_fields:
                    self.log_result("Manifest PWA", "PASS", "Manifest completo y válido")
                else:
                    self.log_result("Manifest PWA", "FAIL", f"Campos faltantes: {missing_fields}")
            else:
                self.log_result("Manifest PWA", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Manifest PWA", "FAIL", str(e))

    def test_service_worker_available(self):
        """Verificar que el Service Worker está disponible"""
        try:
            response = self.client.get('/desur/sw.js')
            if response.status_code == 200:
                sw_content = response.content.decode('utf-8')
                if 'CACHE_NAME' in sw_content and 'install' in sw_content:
                    self.log_result("Service Worker", "PASS", "SW disponible y configurado")
                else:
                    self.log_result("Service Worker", "FAIL", "SW incompleto")
            else:
                self.log_result("Service Worker", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Service Worker", "FAIL", str(e))

    def test_mobile_pages(self):
        """Verificar páginas móviles"""
        mobile_pages = [
            ('/desur/mobile/menu/', 'Menú Móvil'),
            ('/desur/mobile/historial/', 'Historial Móvil'),
            ('/desur/offline/', 'Página Offline'),
            ('/desur/install/', 'Página Instalación')
        ]

        for url, name in mobile_pages:
            try:
                response = self.client.get(url)
                if response.status_code in [200, 302]:  # 302 para páginas que requieren login
                    self.log_result(f"Página {name}", "PASS", f"Disponible (HTTP {response.status_code})")
                else:
                    self.log_result(f"Página {name}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result(f"Página {name}", "FAIL", str(e))

    def test_api_endpoints(self):
        """Verificar endpoints de API"""
        api_endpoints = [
            ('/desur/api/sync/', 'API Sincronización'),
            ('/desur/api/user-data/', 'API Datos Usuario')
        ]

        for url, name in api_endpoints:
            try:
                response = self.client.post(url) if 'sync' in url else self.client.get(url)
                # Esperamos 405 (método no permitido) o 302 (requiere login) - ambos indican que la URL existe
                if response.status_code in [405, 302, 403]:
                    self.log_result(f"{name}", "PASS", f"Endpoint existe (HTTP {response.status_code})")
                else:
                    self.log_result(f"{name}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result(f"{name}", "FAIL", str(e))

    def test_static_files(self):
        """Verificar archivos estáticos necesarios"""
        static_files = [
            'portaldu/desUr/static/sripts/offline-manager.js',
            'portaldu/desUr/static/images/icon-192x192.png',
            'portaldu/desUr/static/images/icon-512x512.png'
        ]

        for file_path in static_files:
            full_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.log_result(f"Archivo {os.path.basename(file_path)}", "PASS", f"Existe ({size} bytes)")
            else:
                self.log_result(f"Archivo {os.path.basename(file_path)}", "FAIL", "No encontrado")

    def test_template_files(self):
        """Verificar templates necesarios"""
        template_files = [
            'portaldu/desUr/templates/mobile/base.html',
            'portaldu/desUr/templates/mobile/menu.html',
            'portaldu/desUr/templates/mobile/historial.html',
            'portaldu/desUr/templates/pwa/offline.html',
            'portaldu/desUr/templates/pwa/install.html',
            'portaldu/desUr/templates/pwa/manifest.json',
            'portaldu/desUr/templates/pwa/sw.js'
        ]

        for file_path in template_files:
            full_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.log_result(f"Template {os.path.basename(file_path)}", "PASS", f"Existe ({size} bytes)")
            else:
                self.log_result(f"Template {os.path.basename(file_path)}", "FAIL", "No encontrado")

    def test_urls_configuration(self):
        """Verificar configuración de URLs"""
        try:
            from portaldu.desUr.urls import urlpatterns
            pwa_urls = [
                'sw.js',
                'manifest.json',
                'offline/',
                'install/',
                'mobile/menu/',
                'mobile/historial/',
                'api/sync/',
                'api/user-data/'
            ]

            configured_urls = [str(pattern.pattern) for pattern in urlpatterns]
            configured_urls_str = ' '.join(configured_urls)

            missing_urls = []
            for url in pwa_urls:
                if url not in configured_urls_str:
                    missing_urls.append(url)

            if not missing_urls:
                self.log_result("Configuración URLs", "PASS", f"{len(pwa_urls)} URLs PWA configuradas")
            else:
                self.log_result("Configuración URLs", "FAIL", f"URLs faltantes: {missing_urls}")

        except Exception as e:
            self.log_result("Configuración URLs", "FAIL", str(e))

    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS PWA PARA DESUR")
        print("=" * 50)

        self.test_manifest_available()
        self.test_service_worker_available()
        self.test_mobile_pages()
        self.test_api_endpoints()
        self.test_static_files()
        self.test_template_files()
        self.test_urls_configuration()

        print("\n" + "=" * 50)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 50)

        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        total = len(self.results)

        print(f"✅ Pruebas exitosas: {passed}")
        print(f"❌ Pruebas fallidas: {failed}")
        print(f"📈 Total: {total}")
        print(f"🎯 Porcentaje de éxito: {(passed/total)*100:.1f}%")

        if failed > 0:
            print("\n🔍 PRUEBAS FALLIDAS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  ❌ {result['test']}: {result['message']}")

        return passed, failed, total

if __name__ == "__main__":
    test_suite = PWATestSuite()
    passed, failed, total = test_suite.run_all_tests()

    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! PWA lista para usar.")
    else:
        print(f"\n⚠️ {failed} pruebas fallaron. Revisa los errores arriba.")

    sys.exit(0 if failed == 0 else 1)
