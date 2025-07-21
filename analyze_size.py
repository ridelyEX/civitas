import os
import sys
from collections import defaultdict

def get_size(path):
    """Obtiene el tamaño de un archivo o directorio"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except (OSError, IOError):
                    pass
        return total
    return 0

def analyze_project():
    """Analiza el tamaño del proyecto por categorías"""
    base_path = os.getcwd()
    categories = {
        'Código fuente': ['.py', '.html', '.css', '.js'],
        'Base de datos': ['.sqlite3', '.db'],
        'Imágenes': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        'PDFs': ['.pdf'],
        'Archivos de configuración': ['.txt', '.json', '.yml', '.yaml', '.ini'],
        'Otros': []
    }

    sizes = defaultdict(int)
    file_counts = defaultdict(int)
    total_size = 0

    for root, dirs, files in os.walk(base_path):
        # Excluir directorios de Python cache y virtual env
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'vrtl', '.git', 'node_modules']]

        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size

                # Categorizar archivo
                file_ext = os.path.splitext(file)[1].lower()
                categorized = False

                for category, extensions in categories.items():
                    if category == 'Otros':
                        continue
                    if file_ext in extensions:
                        sizes[category] += file_size
                        file_counts[category] += 1
                        categorized = True
                        break

                if not categorized:
                    sizes['Otros'] += file_size
                    file_counts['Otros'] += 1

            except (OSError, IOError):
                continue

    # Mostrar resultados
    print("="*60)
    print("ANÁLISIS DE ESPACIO DE ALMACENAMIENTO DEL PROYECTO")
    print("="*60)
    print(f"Tamaño total del proyecto: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print()

    print("Desglose por categorías:")
    print("-" * 40)
    for category in categories.keys():
        if sizes[category] > 0:
            mb_size = sizes[category] / 1024 / 1024
            percentage = (sizes[category] / total_size) * 100
            print(f"{category}: {sizes[category]:,} bytes ({mb_size:.2f} MB) - {percentage:.1f}% - {file_counts[category]} archivos")

    # Análisis específico de media
    print("\n" + "="*60)
    print("ANÁLISIS DETALLADO DE ARCHIVOS MEDIA")
    print("="*60)

    media_path = os.path.join(base_path, 'media')
    if os.path.exists(media_path):
        for subdir in ['documents', 'fotos', 'seguimiento_docs', 'solicitudes']:
            subdir_path = os.path.join(media_path, subdir)
            if os.path.exists(subdir_path):
                subdir_size = get_size(subdir_path)
                file_count = len([f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))])
                print(f"{subdir}/: {subdir_size:,} bytes ({subdir_size/1024/1024:.2f} MB) - {file_count} archivos")

    return total_size, sizes

if __name__ == "__main__":
    analyze_project()
