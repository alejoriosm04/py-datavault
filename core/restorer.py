import os
import zipfile
import tarfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import dask.bag as db
import dask
from datetime import datetime
try:
    from .encryptor import Encryptor
except ImportError:
    from encryptor import Encryptor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Restorer:
    """
    Clase para manejar la restauración de archivos desde backups comprimidos
    y opcionalmente encriptados
    """
    
    SUPPORTED_FORMATS = ['zip', 'tar.gz', 'tar.bz2']
    
    def __init__(self):
        """Inicializa el restaurador"""
        self.encryptor = Encryptor()
        logger.info("Restaurador inicializado")
    
    def detect_archive_format(self, backup_path: str) -> str:
        """
        Detecta el formato del archivo de backup
        
        Args:
            backup_path: Ruta del archivo de backup
            
        Returns:
            Formato detectado ('zip', 'tar.gz', 'tar.bz2')
        """
        backup_path = backup_path.lower()
        
        # Remover extensión .encrypted si existe
        if backup_path.endswith('.encrypted'):
            backup_path = backup_path[:-10]  # Remove '.encrypted'
        
        if backup_path.endswith('.zip'):
            return 'zip'
        elif backup_path.endswith('.tar.gz') or backup_path.endswith('.tgz'):
            return 'tar.gz'
        elif backup_path.endswith('.tar.bz2') or backup_path.endswith('.tbz2'):
            return 'tar.bz2'
        else:
            # Si no podemos detectar por extensión, intentar detectar por contenido
            try:
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    return 'zip'
            except:
                pass
            
            try:
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tf:
                    return 'tar.gz'
            except:
                pass
                
            try:
                import tarfile
                with tarfile.open(backup_path, 'r:bz2') as tf:
                    return 'tar.bz2'
            except:
                pass
            
            raise ValueError(f"Formato de archivo no soportado. Formatos válidos: {self.SUPPORTED_FORMATS}")
    
    def list_archive_contents(self, backup_path: str) -> List[Dict[str, Any]]:
        """
        Lista el contenido de un archivo de backup
        
        Args:
            backup_path: Ruta del archivo de backup
            
        Returns:
            Lista de diccionarios con información de archivos
        """
        format_type = self.detect_archive_format(backup_path)
        contents = []
        
        try:
            if format_type == 'zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    for info in zipf.infolist():
                        if not info.is_dir():
                            contents.append({
                                'name': info.filename,
                                'size': info.file_size,
                                'compressed_size': info.compress_size,
                                'date_time': info.date_time,
                                'is_directory': info.is_dir()
                            })
            
            elif format_type in ['tar.gz', 'tar.bz2']:
                mode = 'r:gz' if format_type == 'tar.gz' else 'r:bz2'
                with tarfile.open(backup_path, mode) as tar:
                    for member in tar.getmembers():
                        if member.isfile():
                            contents.append({
                                'name': member.name,
                                'size': member.size,
                                'compressed_size': member.size,  # TAR no proporciona tamaño comprimido
                                'date_time': datetime.fromtimestamp(member.mtime).timetuple()[:6],
                                'is_directory': member.isdir()
                            })
            
            logger.info(f"Listado completado: {len(contents)} archivos encontrados")
            return contents
            
        except Exception as e:
            logger.error(f"Error listando contenidos de {backup_path}: {str(e)}")
            raise
    
    def restore_backup(self, backup_path: str, restore_path: str, 
                      password: str = None, selected_files: List[str] = None,
                      preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Restaura un backup completo o archivos específicos
        
        Args:
            backup_path: Ruta del archivo de backup
            restore_path: Directorio donde restaurar
            password: Contraseña si el backup está encriptado
            selected_files: Lista de archivos específicos a restaurar (None = todos)
            preserve_structure: Si mantener la estructura de directorios
            
        Returns:
            Información del resultado de la restauración
        """
        start_time = datetime.now()
        
        # Crear directorio de restauración
        os.makedirs(restore_path, exist_ok=True)
        
        # Verificar si el archivo está encriptado
        if self._is_encrypted_file(backup_path):
            if password is None:
                raise ValueError("El archivo está encriptado pero no se proporcionó contraseña")
            
            # Desencriptar primero
            temp_decrypted = os.path.join(restore_path, "temp_decrypted")
            decryption_result = self.encryptor.decrypt_file(backup_path, temp_decrypted, password)
            
            if not decryption_result['success']:
                raise Exception(f"Error desencriptando: {decryption_result['error']}")
            
            backup_to_extract = temp_decrypted
            was_encrypted = True
        else:
            backup_to_extract = backup_path
            was_encrypted = False
        
        try:
            # Detectar formato y extraer
            format_type = self.detect_archive_format(backup_to_extract)
            
            if format_type == 'zip':
                restore_result = self._restore_zip(
                    backup_to_extract, restore_path, selected_files, preserve_structure
                )
            else:
                restore_result = self._restore_tar(
                    backup_to_extract, restore_path, selected_files, preserve_structure, format_type
                )
            
            # Limpiar archivo temporal si se desencriptó
            if was_encrypted and os.path.exists(temp_decrypted):
                os.remove(temp_decrypted)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            restore_result.update({
                'backup_file': backup_path,
                'restore_directory': restore_path,
                'was_encrypted': was_encrypted,
                'total_processing_time': processing_time,
                'format': format_type
            })
            
            logger.info(f"Restauración completada en {processing_time:.2f}s")
            return restore_result
            
        except Exception as e:
            # Limpiar en caso de error
            if was_encrypted and os.path.exists(temp_decrypted):
                os.remove(temp_decrypted)
            raise
    
    def _restore_zip(self, backup_path: str, restore_path: str, 
                    selected_files: List[str], preserve_structure: bool) -> Dict[str, Any]:
        """Restaura desde un archivo ZIP"""
        extracted_files = []
        failed_files = []
        total_size = 0
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Obtener lista de archivos a extraer
            if selected_files:
                files_to_extract = [f for f in zipf.namelist() if f in selected_files]
            else:
                files_to_extract = zipf.namelist()
            
            for file_path in files_to_extract:
                try:
                    # Determinar ruta de destino
                    if preserve_structure:
                        output_path = os.path.join(restore_path, file_path)
                    else:
                        output_path = os.path.join(restore_path, os.path.basename(file_path))
                    
                    # Crear directorios necesarios
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # Extraer archivo
                    with zipf.open(file_path) as source, open(output_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    file_size = os.path.getsize(output_path)
                    total_size += file_size
                    
                    extracted_files.append({
                        'original_path': file_path,
                        'restored_path': output_path,
                        'size': file_size
                    })
                    
                except Exception as e:
                    logger.error(f"Error extrayendo {file_path}: {str(e)}")
                    failed_files.append({
                        'file': file_path,
                        'error': str(e)
                    })
        
        return {
            'extracted_files': extracted_files,
            'failed_files': failed_files,
            'total_files': len(files_to_extract),
            'successful_files': len(extracted_files),
            'failed_count': len(failed_files),
            'total_size': total_size,
            'success': len(failed_files) == 0
        }
    
    def _restore_tar(self, backup_path: str, restore_path: str, 
                    selected_files: List[str], preserve_structure: bool, 
                    format_type: str) -> Dict[str, Any]:
        """Restaura desde un archivo TAR (gz o bz2)"""
        extracted_files = []
        failed_files = []
        total_size = 0
        
        mode = 'r:gz' if format_type == 'tar.gz' else 'r:bz2'
        
        with tarfile.open(backup_path, mode) as tar:
            # Obtener lista de archivos a extraer
            if selected_files:
                members_to_extract = [m for m in tar.getmembers() if m.name in selected_files and m.isfile()]
            else:
                members_to_extract = [m for m in tar.getmembers() if m.isfile()]
            
            for member in members_to_extract:
                try:
                    # Determinar ruta de destino
                    if preserve_structure:
                        output_path = os.path.join(restore_path, member.name)
                    else:
                        output_path = os.path.join(restore_path, os.path.basename(member.name))
                    
                    # Crear directorios necesarios
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # Extraer archivo
                    with tar.extractfile(member) as source, open(output_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    # Preservar timestamps si es posible
                    os.utime(output_path, (member.mtime, member.mtime))
                    
                    file_size = os.path.getsize(output_path)
                    total_size += file_size
                    
                    extracted_files.append({
                        'original_path': member.name,
                        'restored_path': output_path,
                        'size': file_size
                    })
                    
                except Exception as e:
                    logger.error(f"Error extrayendo {member.name}: {str(e)}")
                    failed_files.append({
                        'file': member.name,
                        'error': str(e)
                    })
        
        return {
            'extracted_files': extracted_files,
            'failed_files': failed_files,
            'total_files': len(members_to_extract),
            'successful_files': len(extracted_files),
            'failed_count': len(failed_files),
            'total_size': total_size,
            'success': len(failed_files) == 0
        }
    
    def restore_parallel(self, backup_path: str, restore_path: str,
                        password: str = None, chunk_size: int = 10) -> Dict[str, Any]:
        """
        Restaura un backup usando procesamiento paralelo con Dask
        
        Args:
            backup_path: Ruta del archivo de backup
            restore_path: Directorio donde restaurar
            password: Contraseña si está encriptado
            chunk_size: Tamaño de los chunks para procesamiento paralelo
            
        Returns:
            Información del resultado
        """
        start_time = datetime.now()
        
        # Primero, obtener lista de archivos
        contents = self.list_archive_contents(backup_path)
        file_names = [item['name'] for item in contents]
        
        # Dividir en chunks para procesamiento paralelo
        file_chunks = [file_names[i:i + chunk_size] for i in range(0, len(file_names), chunk_size)]
        
        # Crear tareas con Dask
        tasks = []
        for chunk in file_chunks:
            task = dask.delayed(self.restore_backup)(
                backup_path=backup_path,
                restore_path=restore_path,
                password=password,
                selected_files=chunk,
                preserve_structure=True
            )
            tasks.append(task)
        
        # Ejecutar tareas en paralelo
        results = dask.compute(*tasks)
        
        # Consolidar resultados
        total_extracted = 0
        total_failed = 0
        total_size = 0
        all_extracted_files = []
        all_failed_files = []
        
        for result in results:
            if result['success']:
                total_extracted += result['successful_files']
                total_size += result['total_size']
                all_extracted_files.extend(result['extracted_files'])
            
            total_failed += result['failed_count']
            all_failed_files.extend(result['failed_files'])
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'backup_file': backup_path,
            'restore_directory': restore_path,
            'total_files': len(file_names),
            'successful_files': total_extracted,
            'failed_files': total_failed,
            'total_size': total_size,
            'processing_time': processing_time,
            'extracted_files': all_extracted_files,
            'failed_files': all_failed_files,
            'chunks_processed': len(file_chunks),
            'success': total_failed == 0
        }
    
    def verify_backup_integrity(self, backup_path: str, password: str = None) -> Dict[str, Any]:
        """
        Verifica la integridad de un archivo de backup
        
        Args:
            backup_path: Ruta del archivo de backup
            password: Contraseña si está encriptado
            
        Returns:
            Información sobre la integridad
        """
        try:
            start_time = datetime.now()
            
            # Si está encriptado, verificar desencriptación
            if self._is_encrypted_file(backup_path):
                if password is None:
                    return {'success': False, 'error': 'Archivo encriptado pero sin contraseña'}
                
                # Intentar leer estructura encriptada
                temp_path = backup_path + ".temp_verify"
                decrypt_result = self.encryptor.decrypt_file(backup_path, temp_path, password)
                
                if not decrypt_result['success']:
                    return {'success': False, 'error': f'Error desencriptando: {decrypt_result["error"]}'}
                
                archive_to_check = temp_path
                was_encrypted = True
            else:
                archive_to_check = backup_path
                was_encrypted = False
            
            # Verificar archivo comprimido
            format_type = self.detect_archive_format(archive_to_check)
            file_count = 0
            
            if format_type == 'zip':
                with zipfile.ZipFile(archive_to_check, 'r') as zipf:
                    # Verificar integridad del ZIP
                    bad_files = zipf.testzip()
                    if bad_files:
                        return {'success': False, 'error': f'Archivo corrupto: {bad_files}'}
                    file_count = len(zipf.namelist())
            
            elif format_type in ['tar.gz', 'tar.bz2']:
                mode = 'r:gz' if format_type == 'tar.gz' else 'r:bz2'
                with tarfile.open(archive_to_check, mode) as tar:
                    # Contar miembros
                    file_count = len([m for m in tar.getmembers() if m.isfile()])
            
            # Limpiar archivo temporal
            if was_encrypted and os.path.exists(temp_path):
                os.remove(temp_path)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                'success': True,
                'file_count': file_count,
                'format': format_type,
                'was_encrypted': was_encrypted,
                'verification_time': processing_time,
                'file_size': os.path.getsize(backup_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _is_encrypted_file(self, file_path: str) -> bool:
        """
        Verifica si un archivo está encriptado verificando su estructura
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si está encriptado
        """
        try:
            # Intentar leer como archivo comprimido conocido
            format_type = self.detect_archive_format(file_path)
            
            if format_type == 'zip':
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.testzip()
            elif format_type in ['tar.gz', 'tar.bz2']:
                mode = 'r:gz' if format_type == 'tar.gz' else 'r:bz2'
                with tarfile.open(file_path, mode) as tar:
                    tar.getmembers()
            
            return False  # Si llegamos aquí, no está encriptado
            
        except:
            # Si falla al leer como archivo comprimido, probablemente esté encriptado
            return True


# Funciones de conveniencia
def restore_backup_simple(backup_path: str, restore_path: str, 
                         password: str = None) -> Dict[str, Any]:
    """
    Función de conveniencia para restaurar un backup
    
    Args:
        backup_path: Archivo de backup
        restore_path: Directorio de restauración
        password: Contraseña si está encriptado
        
    Returns:
        Información del resultado
    """
    restorer = Restorer()
    return restorer.restore_backup(backup_path, restore_path, password)


def verify_backup_simple(backup_path: str, password: str = None) -> Dict[str, Any]:
    """
    Función de conveniencia para verificar un backup
    
    Args:
        backup_path: Archivo de backup
        password: Contraseña si está encriptado
        
    Returns:
        Información de la verificación
    """
    restorer = Restorer()
    return restorer.verify_backup_integrity(backup_path, password)


if __name__ == "__main__":
    # Ejemplo de uso
    restorer = Restorer()
    
    # Verificar si hay archivos de backup para probar
    test_backup = "./storage/test_backup.zip"
    restore_dir = "./storage/restored"
    
    if os.path.exists(test_backup):
        print(f"Verificando backup: {test_backup}")
        
        # Verificar integridad
        verification = restorer.verify_backup_integrity(test_backup)
        if verification['success']:
            print(f"✓ Backup válido: {verification['file_count']} archivos")
            
            # Listar contenidos
            contents = restorer.list_archive_contents(test_backup)
            print(f"Contenidos del backup:")
            for item in contents[:5]:  # Mostrar primeros 5
                print(f"  - {item['name']} ({item['size']} bytes)")
            
            # Restaurar
            print(f"\nRestaurando a: {restore_dir}")
            result = restorer.restore_backup(test_backup, restore_dir)
            
            if result['success']:
                print(f"✓ Restauración completada:")
                print(f"  - Archivos restaurados: {result['successful_files']}")
                print(f"  - Tamaño total: {result['total_size']:,} bytes")
                print(f"  - Tiempo: {result['total_processing_time']:.2f}s")
            else:
                print(f"✗ Error en la restauración")
        else:
            print(f"✗ Error verificando backup: {verification['error']}")
    else:
        print(f"No se encontró archivo de backup en: {test_backup}")
        print("Ejecuta primero core/compressor.py para crear un backup de prueba")
