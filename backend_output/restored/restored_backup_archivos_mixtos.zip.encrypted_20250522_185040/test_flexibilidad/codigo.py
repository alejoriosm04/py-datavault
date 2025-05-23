#!/usr/bin/env python3
"""
Archivo de código Python de ejemplo para probar
la flexibilidad del sistema de backup
"""

def funcion_ejemplo():
    """Función de ejemplo para el backup"""
    print("Este es un archivo de código Python")
    print("El sistema puede respaldar cualquier tipo de archivo:")
    
    tipos_soportados = [
        "Código fuente (.py, .js, .java, .cpp, .c, .html, .css)",
        "Documentos (.pdf, .docx, .xlsx, .pptx)",
        "Imágenes (.jpg, .png, .gif, .svg, .bmp)",
        "Videos (.mp4, .avi, .mkv, .mov)",
        "Audio (.mp3, .wav, .flac, .ogg)",
        "Archivos comprimidos (.zip, .rar, .7z, .tar.gz)",
        "Bases de datos (.db, .sqlite, .mdb)",
        "Configuración (.json, .xml, .yaml, .ini)"
    ]
    
    for tipo in tipos_soportados:
        print(f"✓ {tipo}")

if __name__ == "__main__":
    funcion_ejemplo()
    print("\n¡El sistema es completamente flexible!")
    print("Puede respaldar proyectos completos con cualquier combinación de archivos") 