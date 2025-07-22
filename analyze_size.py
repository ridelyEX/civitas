#!/usr/bin/env python3
"""
Análisis de espacio de almacenamiento para Civitas
"""
import os
import sys
from pathlib import Path

def get_folder_size(path):
    """Calcula el tamaño de una carpeta en bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size

def bytes_to_mb(bytes_size):
    """Convierte bytes a MB"""
    return bytes_size / (1024 * 1024)

def analyze_storage():
    """Analiza el uso de almacenamiento del proyecto"""
    base_dir = Path(__file__).parent

    print("=== ANÁLISIS DE ALMACENAMIENTO CIVITAS ===\n")

    # Analizar carpetas principales
    folders_to_analyze = {
        'media/': 'Archivos subidos por usuarios',
        'media/documents/': 'Documentos procesados',
        'media/fotos/': 'Fotografías subidas',
        'media/seguimiento_docs/': 'Documentos de seguimiento',
        'media/solicitudes/': 'Solicitudes generadas',
        'staticfiles/': 'Archivos estáticos (si existe)',
        'logs/': 'Archivos de log',
        'db.sqlite3': 'Base de datos SQLite'
    }

    total_size = 0

    for folder, description in folders_to_analyze.items():
        folder_path = base_dir / folder
        if folder_path.exists():
            if folder_path.is_file():
                size = folder_path.stat().st_size
            else:
                size = get_folder_size(folder_path)

            size_mb = bytes_to_mb(size)
            total_size += size

            print(f"📁 {folder}")
            print(f"   {description}")
            print(f"   Tamaño: {size_mb:.2f} MB")

            # Análisis detallado para media
            if folder == 'media/' and folder_path.is_dir():
                file_count = len(list(folder_path.rglob('*')))
                print(f"   Archivos: {file_count}")
            print()
        else:
            print(f"❌ {folder} - No existe")
            print()

    print(f"💾 TOTAL ACTUAL: {bytes_to_mb(total_size):.2f} MB")
    print()

    # Proyecciones
    print("=== PROYECCIONES DE CRECIMIENTO ===\n")

    # Estimaciones basadas en uso típico
    avg_document_size = 0.5  # MB por documento
    avg_photo_size = 2.0     # MB por foto
    avg_followup_size = 0.3  # MB por seguimiento

    scenarios = {
        "Uso bajo (50 solicitudes/mes)": {
            "docs": 50 * avg_document_size,
            "photos": 100 * avg_photo_size,
            "followups": 25 * avg_followup_size
        },
        "Uso medio (200 solicitudes/mes)": {
            "docs": 200 * avg_document_size,
            "photos": 400 * avg_photo_size,
            "followups": 100 * avg_followup_size
        },
        "Uso alto (500 solicitudes/mes)": {
            "docs": 500 * avg_document_size,
            "photos": 1000 * avg_photo_size,
            "followups": 250 * avg_followup_size
        }
    }

    for scenario, sizes in scenarios.items():
        monthly_growth = sum(sizes.values())
        yearly_growth = monthly_growth * 12

        print(f"📊 {scenario}")
        print(f"   Crecimiento mensual: {monthly_growth:.1f} MB")
        print(f"   Crecimiento anual: {yearly_growth:.1f} MB ({yearly_growth/1024:.1f} GB)")
        print()

    # Recomendaciones
    print("=== RECOMENDACIONES DE ALMACENAMIENTO ===\n")

    current_gb = bytes_to_mb(total_size) / 1024

    if current_gb < 0.5:
        storage_rec = "10-20 GB"
        reason = "Proyecto pequeño, amplio margen de crecimiento"
    elif current_gb < 2:
        storage_rec = "50-100 GB"
        reason = "Crecimiento moderado esperado"
    else:
        storage_rec = "200+ GB"
        reason = "Alto volumen de archivos actual"

    print(f"💡 Almacenamiento recomendado: {storage_rec}")
    print(f"   Razón: {reason}")
    print()

    print("📋 ESTRATEGIAS DE OPTIMIZACIÓN:")
    print("   • Implementar compresión automática de imágenes")
    print("   • Establecer política de retención de archivos")
    print("   • Migrar archivos antiguos a almacenamiento frío")
    print("   • Implementar CDN para archivos estáticos")
    print("   • Monitoreo automático de espacio en disco")

if __name__ == "__main__":
    analyze_storage()
