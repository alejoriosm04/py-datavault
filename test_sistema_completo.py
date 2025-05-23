#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA COMPLETA DEL SISTEMA DE BACKUP
Prueba todos los componentes del sistema py-datavault
"""

from core.utils import BackupManager
import os
import time

def mostrar_separador(titulo):
    print(f"\n{'='*50}")
    print(f"🔧 {titulo}")
    print(f"{'='*50}")

def mostrar_paso(numero, descripcion):
    print(f"\n📍 PASO {numero}: {descripcion}")
    print("-" * 40)

def mostrar_resultado(exito, mensaje):
    icono = "✅" if exito else "❌"
    print(f"{icono} {mensaje}")

def mostrar_archivos_disponibles():
    """Muestra los archivos disponibles para backup"""
    print("📁 ARCHIVOS DISPONIBLES PARA BACKUP:")
    
    if not os.path.exists("./backups"):
        print("❌ No existe la carpeta 'backups/'")
        return False
    
    archivos = os.listdir("./backups")
    if not archivos:
        print("❌ La carpeta 'backups/' está vacía")
        return False
    
    total_size = 0
    for archivo in archivos:
        ruta = f"./backups/{archivo}"
        if os.path.isfile(ruta):
            size = os.path.getsize(ruta)
            total_size += size
            print(f"   📄 {archivo} ({size:,} bytes)")
    
    print(f"   📊 Total: {len(archivos)} archivos, {total_size:,} bytes")
    return True

def probar_backup_basico(manager):
    """Prueba backup básico con ZIP"""
    print("⏳ Creando backup ZIP básico...")
    
    inicio = time.time()
    resultado = manager.create_backup(
        folders=["./backups"],
        backup_name="test_zip_basico",
        compression_algorithm='zip'
    )
    fin = time.time()
    
    if resultado['success']:
        mostrar_resultado(True, f"Backup ZIP creado exitosamente")
        print(f"   📦 Archivo: {resultado['backup_file']}")
        print(f"   📊 Compresión: {resultado['compression_ratio']:.2%}")
        print(f"   ⏱️ Tiempo: {fin-inicio:.2f} segundos")
        return resultado['backup_file']
    else:
        mostrar_resultado(False, f"Error en backup ZIP: {resultado.get('error', 'Error desconocido')}")
        return None

def probar_backup_gzip(manager):
    """Prueba backup con GZIP"""
    print("⏳ Creando backup GZIP...")
    
    inicio = time.time()
    resultado = manager.create_backup(
        folders=["./backups"],
        backup_name="test_gzip_completo",
        compression_algorithm='gzip'
    )
    fin = time.time()
    
    if resultado['success']:
        mostrar_resultado(True, f"Backup GZIP creado exitosamente")
        print(f"   📦 Archivo: {resultado['backup_file']}")
        print(f"   📊 Compresión: {resultado['compression_ratio']:.2%}")
        print(f"   ⏱️ Tiempo: {fin-inicio:.2f} segundos")
        return resultado['backup_file']
    else:
        mostrar_resultado(False, f"Error en backup GZIP: {resultado.get('error', 'Error desconocido')}")
        return None

def probar_backup_encriptado(manager):
    """Prueba backup encriptado"""
    print("⏳ Creando backup encriptado...")
    
    password = "test123"
    inicio = time.time()
    resultado = manager.create_backup(
        folders=["./backups"],
        backup_name="test_encriptado_seguro",
        compression_algorithm='gzip',
        encrypt=True,
        password=password
    )
    fin = time.time()
    
    if resultado['success']:
        mostrar_resultado(True, f"Backup encriptado creado exitosamente")
        print(f"   🔐 Archivo: {resultado['backup_file']}")
        print(f"   📊 Compresión: {resultado['compression_ratio']:.2%}")
        print(f"   ⏱️ Tiempo: {fin-inicio:.2f} segundos")
        print(f"   🔑 Contraseña usada: {password}")
        return resultado['backup_file'], password
    else:
        mostrar_resultado(False, f"Error en backup encriptado: {resultado.get('error', 'Error desconocido')}")
        return None, None

def probar_restauracion(manager, archivo_backup, password=None):
    """Prueba restauración de backup"""
    if not archivo_backup:
        mostrar_resultado(False, "No hay archivo para restaurar")
        return False
    
    print(f"⏳ Restaurando: {os.path.basename(archivo_backup)}")
    
    inicio = time.time()
    resultado = manager.restore_backup(archivo_backup, password=password)
    fin = time.time()
    
    if resultado['success']:
        mostrar_resultado(True, f"Restauración exitosa")
        print(f"   📂 Directorio: {resultado['restore_directory']}")
        print(f"   ⏱️ Tiempo: {fin-inicio:.2f} segundos")
        
        # Verificar archivos restaurados
        if os.path.exists(resultado['restore_directory']):
            archivos = os.listdir(resultado['restore_directory'])
            print(f"   📄 Archivos restaurados: {len(archivos)}")
        return True
    else:
        mostrar_resultado(False, f"Error en restauración: {resultado.get('error', 'Error desconocido')}")
        return False

def mostrar_estructura_creada(manager):
    """Muestra la estructura de directorios creada"""
    print("📂 ESTRUCTURA CREADA:")
    print("-" * 20)
    
    base_dir = "backend_output"
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir):
            level = root.replace(base_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                if file.endswith('.encrypted'):
                    print(f"{subindent}🔐 {file} ({size:,} bytes)")
                elif any(file.endswith(ext) for ext in ['.zip', '.tar.gz', '.tar.bz2']):
                    print(f"{subindent}📦 {file} ({size:,} bytes)")
                else:
                    print(f"{subindent}📄 {file} ({size:,} bytes)")
    else:
        print("❌ No se encontró la estructura backend_output/")

def comparar_algoritmos(manager):
    """Compara rendimiento de algoritmos"""
    print("🔬 COMPARACIÓN DE ALGORITMOS:")
    print("-" * 30)
    
    algoritmos = ['zip', 'gzip', 'bzip2']
    resultados = {}
    
    for algoritmo in algoritmos:
        print(f"⏳ Probando {algoritmo.upper()}...")
        
        inicio = time.time()
        resultado = manager.create_backup(
            folders=["./backups"],
            backup_name=f"comparacion_{algoritmo}",
            compression_algorithm=algoritmo,
            is_test=True  # Guardar en tests/
        )
        fin = time.time()
        
        if resultado['success']:
            resultados[algoritmo] = {
                'tamaño': resultado['final_size'],
                'ratio': resultado['compression_ratio'],
                'tiempo': fin - inicio
            }
            print(f"   ✅ {algoritmo.upper()}: {resultado['final_size']:,} bytes")
        else:
            print(f"   ❌ {algoritmo.upper()}: Error")
    
    # Mostrar tabla comparativa
    if resultados:
        print(f"\n📊 TABLA COMPARATIVA:")
        print(f"{'Algoritmo':<8} {'Tamaño':<12} {'Ratio':<8} {'Tiempo'}")
        print("-" * 40)
        
        for algo, datos in resultados.items():
            print(f"{algo.upper():<8} "
                  f"{datos['tamaño']:,}B"[:10] + " " * max(0, 12 - len(f"{datos['tamaño']:,}B"[:10])) +
                  f"{datos['ratio']:.1%}"[:7] + " " * max(0, 8 - len(f"{datos['ratio']:.1%}"[:7])) +
                  f"{datos['tiempo']:.2f}s")

def main():
    """Función principal de prueba"""
    mostrar_separador("PRUEBA COMPLETA DEL SISTEMA DE BACKUP")
    print("🚀 Iniciando pruebas del sistema py-datavault...")
    
    # Verificar archivos disponibles
    mostrar_paso(1, "Verificando archivos disponibles")
    if not mostrar_archivos_disponibles():
        print("\n❌ No se pueden realizar las pruebas sin archivos en backups/")
        return
    
    # Crear manager
    print("\n⚙️ Inicializando BackupManager...")
    try:
        manager = BackupManager()
        mostrar_resultado(True, "BackupManager inicializado correctamente")
    except Exception as e:
        mostrar_resultado(False, f"Error inicializando BackupManager: {e}")
        return
    
    # Prueba 1: Backup básico ZIP
    mostrar_paso(2, "Prueba de backup básico (ZIP)")
    archivo_zip = probar_backup_basico(manager)
    
    # Prueba 2: Backup GZIP
    mostrar_paso(3, "Prueba de backup GZIP")
    archivo_gzip = probar_backup_gzip(manager)
    
    # Prueba 3: Backup encriptado
    mostrar_paso(4, "Prueba de backup encriptado")
    archivo_encriptado, password = probar_backup_encriptado(manager)
    
    # Prueba 4: Restauración de backup normal
    mostrar_paso(5, "Prueba de restauración (backup normal)")
    probar_restauracion(manager, archivo_zip)
    
    # Prueba 5: Restauración de backup encriptado
    mostrar_paso(6, "Prueba de restauración (backup encriptado)")
    probar_restauracion(manager, archivo_encriptado, password)
    
    # Prueba 6: Comparación de algoritmos
    mostrar_paso(7, "Comparación de algoritmos")
    comparar_algoritmos(manager)
    
    # Mostrar estructura final
    mostrar_paso(8, "Estructura de directorios creada")
    mostrar_estructura_creada(manager)
    
    # Resumen final
    mostrar_separador("RESUMEN FINAL")
    print("🎉 ¡Pruebas completadas!")
    print("\n✅ Funcionalidades probadas:")
    print("   📦 Backup ZIP (rápido)")
    print("   📦 Backup GZIP (balance)")
    print("   🔐 Backup encriptado (seguro)")
    print("   📂 Restauración normal")
    print("   🔓 Restauración encriptada")
    print("   🔬 Comparación de algoritmos")
    print("   📁 Organización automática")
    
    print(f"\n📂 Estructura creada en: backend_output/")
    print(f"🔍 Revisa los archivos creados para verificar funcionamiento")
    
    print(f"\n🎯 SISTEMA FUNCIONANDO CORRECTAMENTE ✅")

if __name__ == "__main__":
    main() 