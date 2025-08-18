#!/usr/bin/env python3
"""
Script para generar iconos PWA para DesUr
Crea iconos en diferentes tamaños para funcionamiento como aplicación nativa
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Configuración de colores y diseño
PRIMARY_COLOR = "#007bff"
SECONDARY_COLOR = "#ffffff"
TEXT_COLOR = "#ffffff"

# Tamaños de iconos necesarios para PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def create_base_icon(size):
    """Crear icono base con diseño de DesUr"""
    # Crear imagen con fondo azul
    img = Image.new('RGB', (size, size), PRIMARY_COLOR)
    draw = ImageDraw.Draw(img)

    # Dibujar forma de edificio/desarrollo urbano
    margin = size // 8

    # Edificio principal (rectángulo)
    building_width = size - (margin * 2)
    building_height = size - (margin * 2)

    draw.rectangle([
        margin, margin,
        margin + building_width, margin + building_height
    ], fill=SECONDARY_COLOR, outline=PRIMARY_COLOR, width=3)

    # Detalles del edificio (ventanas)
    window_size = building_width // 6
    for row in range(3):
        for col in range(3):
            x = margin + (col + 1) * (building_width // 4)
            y = margin + (row + 1) * (building_height // 4)
            draw.rectangle([
                x, y,
                x + window_size, y + window_size
            ], fill=PRIMARY_COLOR)

    # Agregar texto "DesUr" si el icono es suficientemente grande
    if size >= 128:
        try:
            # Intentar usar una fuente
            font_size = max(12, size // 16)
            font = ImageFont.load_default()

            text = "DesUr"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Posicionar texto en la parte inferior
            text_x = (size - text_width) // 2
            text_y = size - margin - text_height - 5

            # Fondo para el texto
            draw.rectangle([
                text_x - 5, text_y - 2,
                text_x + text_width + 5, text_y + text_height + 2
            ], fill=PRIMARY_COLOR)

            draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=font)

        except Exception as e:
            print(f"No se pudo agregar texto al icono de {size}px: {e}")

    return img

def create_maskable_icon(size):
    """Crear icono adaptativo (maskable) con área segura"""
    # Los iconos maskable necesitan un 10% de margen seguro
    safe_zone = int(size * 0.1)

    # Crear fondo completo
    img = Image.new('RGB', (size, size), PRIMARY_COLOR)

    # Crear el icono principal en el área segura
    inner_size = size - (safe_zone * 2)
    inner_icon = create_base_icon(inner_size)

    # Pegar el icono centrado
    img.paste(inner_icon, (safe_zone, safe_zone))

    return img

def create_pwa_icons():
    """Generar todos los iconos PWA necesarios"""
    base_path = "C:/Users/Usuario/Documents/pagTramites/tramites/civitas/portaldu/desUr/static/images"

    # Crear directorio si no existe
    os.makedirs(base_path, exist_ok=True)

    print("Generando iconos PWA para DesUr...")

    for size in ICON_SIZES:
        # Icono normal
        icon = create_base_icon(size)
        icon_path = os.path.join(base_path, f"icon-{size}x{size}.png")
        icon.save(icon_path, "PNG", optimize=True)
        print(f"✓ Creado: icon-{size}x{size}.png")

        # Icono maskable (adaptativo)
        maskable_icon = create_maskable_icon(size)
        maskable_path = os.path.join(base_path, f"icon-{size}x{size}-maskable.png")
        maskable_icon.save(maskable_path, "PNG", optimize=True)
        print(f"✓ Creado: icon-{size}x{size}-maskable.png")

    # Crear favicon
    favicon = create_base_icon(32)
    favicon_path = os.path.join(base_path, "favicon.ico")
    favicon.save(favicon_path, "ICO")
    print("✓ Creado: favicon.ico")

    # Crear apple-touch-icon
    apple_icon = create_base_icon(180)
    apple_path = os.path.join(base_path, "apple-touch-icon.png")
    apple_icon.save(apple_path, "PNG", optimize=True)
    print("✓ Creado: apple-touch-icon.png")

    print("\n🎉 Todos los iconos PWA han sido generados exitosamente!")
    print(f"📁 Ubicación: {base_path}")

def create_screenshots():
    """Crear capturas de pantalla de ejemplo para PWA"""
    base_path = "C:/Users/Usuario/Documents/pagTramites/tramites/civitas/portaldu/desUr/static/images"

    # Screenshot desktop (1280x720)
    desktop_img = Image.new('RGB', (1280, 720), SECONDARY_COLOR)
    desktop_draw = ImageDraw.Draw(desktop_img)

    # Header
    desktop_draw.rectangle([0, 0, 1280, 80], fill=PRIMARY_COLOR)
    desktop_draw.text((20, 30), "DesUr - Portal de Desarrollo Urbano", fill=TEXT_COLOR)

    # Contenido de ejemplo
    desktop_draw.text((20, 120), "Sistema de trámites de desarrollo urbano", fill="#333333")
    desktop_draw.text((20, 160), "• Gestión de solicitudes", fill="#666666")
    desktop_draw.text((20, 190), "• Seguimiento de trámites", fill="#666666")
    desktop_draw.text((20, 220), "• Funciona sin conexión", fill="#666666")

    desktop_path = os.path.join(base_path, "screenshot-desktop.png")
    desktop_img.save(desktop_path, "PNG", optimize=True)
    print("✓ Creado: screenshot-desktop.png")

    # Screenshot mobile (375x667)
    mobile_img = Image.new('RGB', (375, 667), SECONDARY_COLOR)
    mobile_draw = ImageDraw.Draw(mobile_img)

    # Header móvil
    mobile_draw.rectangle([0, 0, 375, 60], fill=PRIMARY_COLOR)
    mobile_draw.text((20, 20), "DesUr Mobile", fill=TEXT_COLOR)

    # Contenido móvil
    mobile_draw.text((20, 100), "Trámites de Desarrollo Urbano", fill="#333333")
    mobile_draw.text((20, 140), "• Interfaz optimizada para móvil", fill="#666666")
    mobile_draw.text((20, 170), "• Funcionalidad offline", fill="#666666")
    mobile_draw.text((20, 200), "• Instalable como app", fill="#666666")

    mobile_path = os.path.join(base_path, "screenshot-mobile.png")
    mobile_img.save(mobile_path, "PNG", optimize=True)
    print("✓ Creado: screenshot-mobile.png")

if __name__ == "__main__":
    try:
        create_pwa_icons()
        create_screenshots()

        print("\n📱 Los iconos están listos para la PWA DesUr")
        print("🔧 La aplicación ahora puede instalarse como app nativa")
        print("🌐 Funciona sin conexión WiFi en dispositivos móviles")

    except Exception as e:
        print(f"❌ Error generando iconos: {e}")
        print("Asegúrate de tener Pillow instalado: pip install Pillow")
