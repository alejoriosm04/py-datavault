import os
import shutil
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from .compressor import Compressor, compress_backup
    from .encryptor import Encryptor, encrypt_backup_file, decrypt_backup_file
    from .restorer import Restorer, restore_backup_simple, verify_backup_simple
except ImportError:
    from compressor import Compressor, compress_backup
    from encryptor import Encryptor, encrypt_backup_file, decrypt_backup_file
    from restorer import Restorer, restore_backup_simple, verify_backup_simple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    """
    Clase coordinadora principal para gestionar todo el proceso de backup y restauración
    Integra compresión, encriptación y restauración con paralelismo
    """
    
    def __init__(self, working_directory: str = None, output_base_dir: str = None):
        """
        Inicializa el gestor de backups
        
        Args:
            working_directory: Directorio de trabajo para archivos temporales
            output_base_dir: Directorio base para organizar las salidas
        """
        self.working_directory = working_directory or os.path.join(os.getcwd(), "temp_backup")
        self.output_base_dir = output_base_dir or os.path.join(os.getcwd(), "backend_output")
        
        # Crear estructura de directorios organizada
        self._create_output_structure()
        
        self.compressor = Compressor()
        self.encryptor = Encryptor()
        self.restorer = Restorer()
        
        # Crear directorio de trabajo si no existe
        os.makedirs(self.working_directory, exist_ok=True)
        
        logger.info(f"BackupManager inicializado")
        logger.info(f"  - Directorio trabajo: {self.working_directory}")
        logger.info(f"  - Directorio salidas: {self.output_base_dir}")
    
    def _create_output_structure(self):
        """Crea la estructura de directorios organizada para las salidas"""
        self.dirs = {
            'base': self.output_base_dir,
            'compressed': {
                'zip': os.path.join(self.output_base_dir, "compressed", "zip"),
                'gzip': os.path.join(self.output_base_dir, "compressed", "gzip"), 
                'bzip2': os.path.join(self.output_base_dir, "compressed", "bzip2")
            },
            'encrypted': os.path.join(self.output_base_dir, "encrypted"),
            'restored': os.path.join(self.output_base_dir, "restored"),
            'tests': os.path.join(self.output_base_dir, "tests")
        }
        
        # Crear todos los directorios
        for path in [self.dirs['base'], self.dirs['encrypted'], self.dirs['restored'], self.dirs['tests']]:
            os.makedirs(path, exist_ok=True)
            
        for compression_dir in self.dirs['compressed'].values():
            os.makedirs(compression_dir, exist_ok=True)
    
    def _get_output_path(self, compression_algorithm: str, encrypted: bool, is_test: bool = False) -> str:
        """
        Determina la ruta de salida apropiada según el tipo de backup
        
        Args:
            compression_algorithm: Algoritmo usado
            encrypted: Si está encriptado
            is_test: Si es un archivo de prueba
            
        Returns:
            Ruta del directorio de salida apropiado
        """
        if is_test:
            return self.dirs['tests']
        elif encrypted:
            return self.dirs['encrypted']
        else:
            return self.dirs['compressed'][compression_algorithm]
    
    def create_backup(self, folders: List[str], output_path: str = None, 
                     backup_name: str = None, compression_algorithm: str = 'zip',
                     encrypt: bool = False, password: str = None, 
                     is_test: bool = False) -> Dict[str, Any]:
        """
        Crea un backup completo con compresión y encriptación opcional
        
        Args:
            folders: Lista de carpetas a respaldar
            output_path: Directorio donde guardar el backup (si None, usa estructura organizada)
            backup_name: Nombre del backup (si None, se genera automáticamente)
            compression_algorithm: Algoritmo de compresión ('zip', 'gzip', 'bzip2')
            encrypt: Si encriptar el backup
            password: Contraseña para encriptación (requerida si encrypt=True)
            is_test: Si es un backup de prueba
            
        Returns:
            Diccionario con información detallada del proceso
        """
        if encrypt and not password:
            raise ValueError("Se requiere contraseña para encriptar el backup")
        
        start_time = datetime.now()
        
        # Generar nombre si no se proporcionó
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        # Determinar directorio de salida
        if output_path is None:
            output_path = self._get_output_path(compression_algorithm, encrypt, is_test)
        
        logger.info(f"Iniciando creación de backup: {backup_name}")
        logger.info(f"  - Algoritmo: {compression_algorithm}")
        logger.info(f"  - Encriptado: {encrypt}")
        logger.info(f"  - Directorio salida: {output_path}")
        
        try:
            # Paso 1: Comprimir archivos
            logger.info("Paso 1/3: Comprimiendo archivos...")
            self.compressor.algorithm = compression_algorithm
            
            compression_result = self.compressor.compress_folders(
                folders=folders,
                output_path=self.working_directory,
                base_name=backup_name
            )
            
            if not compression_result['success']:
                raise Exception("Error durante la compresión")
            
            compressed_file = compression_result['output_file']
            
            # Paso 2: Encriptar si se solicita
            final_file = compressed_file
            encryption_result = None
            
            if encrypt:
                logger.info("Paso 2/3: Encriptando backup...")
                encrypted_file = compressed_file + ".encrypted"
                
                encryption_result = self.encryptor.encrypt_file(
                    input_path=compressed_file,
                    output_path=encrypted_file,
                    password=password
                )
                
                if not encryption_result['success']:
                    raise Exception(f"Error durante la encriptación: {encryption_result['error']}")
                
                final_file = encrypted_file
                
                # Limpiar archivo comprimido temporal
                os.remove(compressed_file)
            
            # Paso 3: Mover a ubicación final
            logger.info("Paso 3/3: Finalizando backup...")
            final_backup_path = os.path.join(output_path, os.path.basename(final_file))
            
            # Crear directorio de salida si no existe
            os.makedirs(output_path, exist_ok=True)
            
            # Mover archivo a ubicación final
            shutil.move(final_file, final_backup_path)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Compilar resultado final
            result = {
                'backup_file': final_backup_path,
                'backup_name': backup_name,
                'folders_backed_up': folders,
                'compression_algorithm': compression_algorithm,
                'encrypted': encrypt,
                'total_files': compression_result['total_files'],
                'successful_files': compression_result['successful_files'],
                'failed_files': compression_result['failed_files'],
                'original_size': compression_result['original_size'],
                'final_size': os.path.getsize(final_backup_path),
                'compression_ratio': compression_result['compression_ratio'],
                'total_processing_time': total_time,
                'compression_time': compression_result['processing_time'],
                'encryption_time': encryption_result['processing_time'] if encryption_result else 0,
                'output_directory': output_path,
                'success': True
            }
            
            logger.info(f"Backup creado exitosamente: {final_backup_path}")
            logger.info(f"Tiempo total: {total_time:.2f}s | Archivos: {result['successful_files']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creando backup: {str(e)}")
            
            # Limpiar archivos temporales en caso de error
            self._cleanup_temp_files()
            
            return {
                'error': str(e),
                'success': False,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    def restore_backup(self, backup_path: str, restore_path: str = None,
                      password: str = None, selected_files: List[str] = None,
                      preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Restaura un backup (con desencriptación automática si es necesario)
        
        Args:
            backup_path: Ruta del archivo de backup
            restore_path: Directorio donde restaurar (si None, usa estructura organizada)
            password: Contraseña si el backup está encriptado
            selected_files: Archivos específicos a restaurar (None = todos)
            preserve_structure: Mantener estructura de directorios
            
        Returns:
            Información del resultado
        """
        # Si no se especifica restore_path, usar estructura organizada
        if restore_path is None:
            backup_filename = os.path.basename(backup_path)
            restore_path = os.path.join(self.dirs['restored'], f"restored_{backup_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        logger.info(f"Iniciando restauración desde: {backup_path}")
        logger.info(f"Restaurando a: {restore_path}")
        
        try:
            result = self.restorer.restore_backup(
                backup_path=backup_path,
                restore_path=restore_path,
                password=password,
                selected_files=selected_files,
                preserve_structure=preserve_structure
            )
            
            if result['success']:
                logger.info(f"Restauración completada: {result['successful_files']} archivos")
            
            return result
            
        except Exception as e:
            logger.error(f"Error durante la restauración: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def verify_backup(self, backup_path: str, password: str = None) -> Dict[str, Any]:
        """
        Verifica la integridad de un backup
        
        Args:
            backup_path: Ruta del archivo de backup
            password: Contraseña si está encriptado
            
        Returns:
            Información de la verificación
        """
        logger.info(f"Verificando backup: {backup_path}")
        
        result = self.restorer.verify_backup_integrity(backup_path, password)
        
        if result['success']:
            logger.info(f"✓ Backup válido: {result['file_count']} archivos")
        else:
            logger.error(f"✗ Backup inválido: {result['error']}")
        
        return result
    
    def list_backup_contents(self, backup_path: str, password: str = None) -> List[Dict[str, Any]]:
        """
        Lista el contenido de un backup sin extraerlo
        
        Args:
            backup_path: Ruta del archivo de backup
            password: Contraseña si está encriptado
            
        Returns:
            Lista de archivos en el backup
        """
        try:
            # Si está encriptado, desencriptar temporalmente
            if self.restorer._is_encrypted_file(backup_path):
                if password is None:
                    raise ValueError("Backup encriptado requiere contraseña")
                
                temp_file = os.path.join(self.working_directory, "temp_list")
                decrypt_result = self.encryptor.decrypt_file(backup_path, temp_file, password)
                
                if not decrypt_result['success']:
                    raise Exception(f"Error desencriptando: {decrypt_result['error']}")
                
                contents = self.restorer.list_archive_contents(temp_file)
                os.remove(temp_file)  # Limpiar
                
            else:
                contents = self.restorer.list_archive_contents(backup_path)
            
            logger.info(f"Listado completado: {len(contents)} archivos")
            return contents
            
        except Exception as e:
            logger.error(f"Error listando contenidos: {str(e)}")
            raise
    
    def get_backup_info(self, backup_path: str, password: str = None) -> Dict[str, Any]:
        """
        Obtiene información completa sobre un backup
        
        Args:
            backup_path: Ruta del archivo de backup
            password: Contraseña si está encriptado
            
        Returns:
            Información detallada del backup
        """
        try:
            # Información básica del archivo
            file_stats = os.stat(backup_path)
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime)
            
            # Verificar integridad
            verification = self.verify_backup(backup_path, password)
            
            # Listar contenidos si es válido
            contents = []
            if verification['success']:
                try:
                    contents = self.list_backup_contents(backup_path, password)
                except:
                    pass  # No crítico si falla el listado
            
            return {
                'file_path': backup_path,
                'file_size': file_size,
                'file_size_mb': file_size / (1024 * 1024),
                'modified_time': modified_time,
                'is_encrypted': verification.get('was_encrypted', False),
                'format': verification.get('format', 'unknown'),
                'is_valid': verification['success'],
                'file_count': verification.get('file_count', 0),
                'contents_preview': contents[:10] if contents else [],  # Primeros 10 archivos
                'total_files_in_backup': len(contents),
                'verification_error': verification.get('error')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información del backup: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def show_output_structure(self):
        """Muestra la estructura de directorios de salida"""
        print("\n📁 ESTRUCTURA DE DIRECTORIOS DE SALIDA:")
        print(f"📂 {self.output_base_dir}/")
        print("├── 📁 compressed/")
        print("│   ├── 📁 zip/          (archivos .zip)")
        print("│   ├── 📁 gzip/         (archivos .tar.gz)")
        print("│   └── 📁 bzip2/        (archivos .tar.bz2)")
        print("├── 📁 encrypted/        (archivos .encrypted)")
        print("├── 📁 restored/         (archivos restaurados)")
        print("└── 📁 tests/           (archivos de prueba)")
    
    def _cleanup_temp_files(self):
        """Limpia archivos temporales del directorio de trabajo"""
        try:
            if os.path.exists(self.working_directory):
                for file in os.listdir(self.working_directory):
                    file_path = os.path.join(self.working_directory, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.debug(f"Archivo temporal eliminado: {file}")
        except Exception as e:
            logger.warning(f"Error limpiando archivos temporales: {str(e)}")
    
    def cleanup(self):
        """Limpia completamente el directorio de trabajo"""
        try:
            if os.path.exists(self.working_directory):
                shutil.rmtree(self.working_directory)
                logger.info("Directorio de trabajo limpiado")
        except Exception as e:
            logger.warning(f"Error limpiando directorio de trabajo: {str(e)}")
    
    def __del__(self):
        """Limpia automáticamente al destruir la instancia"""
        self._cleanup_temp_files()


# Funciones de conveniencia para uso directo
def create_simple_backup(folders: List[str], output_path: str = None, 
                        backup_name: str = None, encrypt: bool = False,
                        password: str = None) -> Dict[str, Any]:
    """
    Función simple para crear un backup
    
    Args:
        folders: Carpetas a respaldar
        output_path: Donde guardar el backup (si None, usa estructura organizada)
        backup_name: Nombre del backup
        encrypt: Si encriptar
        password: Contraseña si se encripta
        
    Returns:
        Resultado del backup
    """
    manager = BackupManager()
    try:
        return manager.create_backup(
            folders=folders,
            output_path=output_path,
            backup_name=backup_name,
            encrypt=encrypt,
            password=password
        )
    finally:
        manager.cleanup()


def restore_simple_backup(backup_path: str, restore_path: str = None,
                         password: str = None) -> Dict[str, Any]:
    """
    Función simple para restaurar un backup
    
    Args:
        backup_path: Archivo de backup
        restore_path: Donde restaurar (si None, usa estructura organizada)
        password: Contraseña si está encriptado
        
    Returns:
        Resultado de la restauración
    """
    manager = BackupManager()
    try:
        return manager.restore_backup(backup_path, restore_path, password)
    finally:
        manager.cleanup()


if __name__ == "__main__":
    # Ejemplo de uso completo
    manager = BackupManager()
    
    # Mostrar estructura
    manager.show_output_structure()
    
    # Carpetas de prueba
    test_folders = ["./backups"]
    backup_name = "demo_organizado"
    password = "mi_password_seguro"
    
    try:
        print("\n=== DEMO DEL SISTEMA ORGANIZADO ===\n")
        
        # 1. Crear backup ZIP sin encriptar
        print("1. Creando backup ZIP...")
        result_zip = manager.create_backup(
            folders=test_folders,
            backup_name="demo_zip",
            compression_algorithm='zip',
            encrypt=False
        )
        
        if result_zip['success']:
            print(f"✓ ZIP creado en: {result_zip['backup_file']}")
        
        # 2. Crear backup GZIP encriptado
        print("\n2. Creando backup GZIP encriptado...")
        result_gzip = manager.create_backup(
            folders=test_folders,
            backup_name="demo_gzip_encrypted",
            compression_algorithm='gzip',
            encrypt=True,
            password=password
        )
        
        if result_gzip['success']:
            print(f"✓ GZIP encriptado creado en: {result_gzip['backup_file']}")
        
        # 3. Mostrar organización
        print(f"\n3. Estructura creada:")
        manager.show_output_structure()
        
        # 4. Restaurar
        print(f"\n4. Restaurando backup encriptado...")
        restore_result = manager.restore_backup(result_gzip['backup_file'], password=password)
        
        if restore_result['success']:
            print(f"✓ Restaurado en: {restore_result['restore_directory']}")
            
    except Exception as e:
        print(f"✗ Error en el demo: {str(e)}")
    
    finally:
        manager.cleanup()
        print(f"\n=== Demo completado ===")
