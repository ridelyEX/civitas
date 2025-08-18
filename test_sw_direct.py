#!/usr/bin/env python3
"""
Script para verificar que el Service Worker se esté sirviendo correctamente
"""

import requests
import sys

def test_service_worker():
    """Prueba directa del Service Worker"""
    base_url = "http://127.0.0.1:8000"

    print("🔧 Verificando Service Worker...")

    # Probar diferentes rutas del Service Worker
    test_urls = [
        f"{base_url}/static/sw.js",
        f"{base_url}/sw.js",
        f"{base_url}/ageo/sw.js"
    ]

    for url in test_urls:
        try:
            print(f"\n📡 Probando: {url}")
            response = requests.get(url, timeout=5)

            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Cache-Control: {response.headers.get('cache-control', 'N/A')}")

            if response.status_code == 200:
                content_preview = response.text[:100].replace('\n', ' ')
                print(f"   Contenido: {content_preview}...")

                if 'Ageo SW' in response.text:
                    print("   ✅ Service Worker encontrado y válido")
                    return True
                else:
                    print("   ⚠️  Archivo encontrado pero contenido incorrecto")
            else:
                print(f"   ❌ Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")

    return False

def test_install_page():
    """Prueba la página de instalación PWA"""
    print("\n📱 Verificando página de instalación...")

    try:
        response = requests.get("http://127.0.0.1:8000/ageo/install/", timeout=10)

        if response.status_code == 200:
            print("   ✅ Página de instalación accesible")

            # Verificar que contiene elementos PWA importantes
            content = response.text
            checks = {
                'Service Worker script': 'serviceWorker.register' in content,
                'PWA detection': 'checkServiceWorker' in content,
                'Device detection': 'detectDevice' in content,
                'Install button': 'installBtn' in content
            }

            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")

            return all(checks.values())
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Verificando configuración PWA de DesUr")
    print("=" * 50)

    sw_ok = test_service_worker()
    install_ok = test_install_page()

    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)

    if sw_ok and install_ok:
        print("🎉 ¡Todo funciona correctamente!")
        print("✨ La PWA está lista para usar")
        print("\n🔗 Accede a: http://127.0.0.1:8000/ageo/install/")
        sys.exit(0)
    else:
        print("⚠️  Hay problemas que necesitan corrección:")
        if not sw_ok:
            print("   • Service Worker no se está sirviendo correctamente")
        if not install_ok:
            print("   • Página de instalación tiene problemas")
        sys.exit(1)
