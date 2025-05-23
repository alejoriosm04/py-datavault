import os
import zipfile
import gzip
import bz2
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
import dask.bag as db
from dask.distributed import as_completed
import dask
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Compressor:
    """
    Clase para manejar la compresión de archivos con diferentes algoritmos
    y paralelismo usando Dask
    """
    
    SUPPORTED_ALGORITHMS = ['zip', 'gzip', 'bzip2']
    
    def __init__(self, algorithm: str = 'zip'):
        """
        Inicializa el compresor con el algoritmo especificado
        
        Args:
            algorithm: Algoritmo de compresión ('zip', 'gzip', 'bzip2')
        """
        if algorithm.lower() not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Algoritmo no soportado. Use uno de: {self.SUPPORTED_ALGORITHMS}")
        
        self.algorithm = algorithm.lower()
        logger.info(f"Compressor inicializado con algoritmo: {self.algorithm}")
    
    def collect_files(self, folders: List[str]) -> List[str]:
        """
        Recolecta todos los archivos de las carpetas especificadas
        
        Args:
            folders: Lista de rutas de carpetas a respaldar
            
        Returns:
            Lista de rutas de archivos a comprimir
        """
        all_files = []
        
        for folder in folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                logger.warning(f"La carpeta {folder} no existe, saltando...")
                continue
                
            if folder_path.is_file():
                all_files.append(str(folder_path))
            else:
                # Recolectar todos los archivos recursivamente
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        all_files.append(str(file_path))
        
        logger.info(f"Se encontraron {len(all_files)} archivos para respaldar")
        return all_files
    
    def _compress_file_chunk(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprime un archivo individual (para uso con Dask)
        
        Args:
            file_info: Diccionario con información del archivo
            
        Returns:
            Resultado de la compresión
        """
        file_path = file_info['path']
        relative_path = file_info['relative_path']
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            if self.algorithm == 'gzip':
                compressed_data = gzip.compress(data)
            elif self.algorithm == 'bzip2':
                compressed_data = bz2.compress(data)
            else:  # zip handled separately
                compressed_data = data
            
            original_size = len(data)
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            return {
                'relative_path': relative_path,
                'data': compressed_data,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error comprimiendo {file_path}: {str(e)}")
            return {
                'relative_path': relative_path,
                'error': str(e),
                'success': False
            }
    
    def compress_folders(self, folders: List[str], output_path: str, 
                        base_name: str = None) -> Dict[str, Any]:
        """
        Comprime múltiples carpetas en un archivo de backup usando paralelismo
        
        Args:
            folders: Lista de carpetas a comprimir
            output_path: Ruta donde guardar el archivo comprimido
            base_name: Nombre base para el archivo (si None, se genera automáticamente)
            
        Returns:
            Diccionario con información del resultado
        """
        if base_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"backup_{timestamp}"
        
        # Determinar extensión según algoritmo
        extensions = {'zip': '.zip', 'gzip': '.tar.gz', 'bzip2': '.tar.bz2'}
        output_file = os.path.join(output_path, f"{base_name}{extensions[self.algorithm]}")
        
        # Recolectar archivos
        all_files = self.collect_files(folders)
        if not all_files:
            raise ValueError("No se encontraron archivos para comprimir")
        
        # Preparar información de archivos para procesamiento paralelo
        file_infos = []
        for file_path in all_files:
            # Calcular ruta relativa para mantener estructura
            relative_path = os.path.relpath(file_path, os.path.commonpath(folders))
            file_infos.append({
                'path': file_path,
                'relative_path': relative_path
            })
        
        start_time = datetime.now()
        logger.info(f"Iniciando compresión de {len(file_infos)} archivos con {self.algorithm}")
        
        try:
            if self.algorithm == 'zip':
                return self._compress_zip(file_infos, output_file, start_time)
            else:
                return self._compress_tar(file_infos, output_file, start_time)
                
        except Exception as e:
            logger.error(f"Error durante la compresión: {str(e)}")
            raise
    
    def _compress_zip(self, file_infos: List[Dict], output_file: str, 
                     start_time: datetime) -> Dict[str, Any]:
        """Comprime archivos usando ZIP con paralelismo"""
        
        # Usar Dask para procesar archivos en paralelo
        file_bag = db.from_sequence(file_infos, npartitions=min(len(file_infos), 4))
        
        # Procesar archivos en paralelo
        results = file_bag.map(self._compress_file_chunk).compute()
        
        # Crear archivo ZIP
        total_original_size = 0
        total_compressed_size = 0
        successful_files = 0
        
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for result in results:
                if result['success']:
                    zipf.writestr(result['relative_path'], result['data'])
                    total_original_size += result['original_size']
                    total_compressed_size += result['compressed_size']
                    successful_files += 1
                else:
                    logger.error(f"Falló: {result['relative_path']} - {result['error']}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'algorithm': self.algorithm,
            'output_file': output_file,
            'total_files': len(file_infos),
            'successful_files': successful_files,
            'failed_files': len(file_infos) - successful_files,
            'original_size': total_original_size,
            'compressed_size': os.path.getsize(output_file),
            'compression_ratio': os.path.getsize(output_file) / total_original_size if total_original_size > 0 else 0,
            'processing_time': processing_time,
            'success': True
        }
    
    def _compress_tar(self, file_infos: List[Dict], output_file: str, 
                     start_time: datetime) -> Dict[str, Any]:
        """Comprime archivos usando TAR con GZIP o BZIP2"""
        import tarfile
        
        mode = 'w:gz' if self.algorithm == 'gzip' else 'w:bz2'
        total_original_size = 0
        successful_files = 0
        
        with tarfile.open(output_file, mode) as tar:
            for file_info in file_infos:
                try:
                    file_path = file_info['path']
                    relative_path = file_info['relative_path']
                    
                    tar.add(file_path, arcname=relative_path)
                    total_original_size += os.path.getsize(file_path)
                    successful_files += 1
                    
                except Exception as e:
                    logger.error(f"Error agregando {file_info['path']}: {str(e)}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'algorithm': self.algorithm,
            'output_file': output_file,
            'total_files': len(file_infos),
            'successful_files': successful_files,
            'failed_files': len(file_infos) - successful_files,
            'original_size': total_original_size,
            'compressed_size': os.path.getsize(output_file),
            'compression_ratio': os.path.getsize(output_file) / total_original_size if total_original_size > 0 else 0,
            'processing_time': processing_time,
            'success': True
        }

# Función de conveniencia para uso directo
def compress_backup(folders: List[str], output_path: str, algorithm: str = 'zip', 
                   backup_name: str = None) -> Dict[str, Any]:
    """
    Función de conveniencia para crear un backup comprimido
    
    Args:
        folders: Lista de carpetas a respaldar
        output_path: Directorio donde guardar el backup
        algorithm: Algoritmo de compresión ('zip', 'gzip', 'bzip2')
        backup_name: Nombre del archivo de backup
        
    Returns:
        Información del resultado de la compresión
    """
    compressor = Compressor(algorithm)
    return compressor.compress_folders(folders, output_path, backup_name)


if __name__ == "__main__":
    # Ejemplo de uso
    folders_to_backup = ["./backups"]
    output_directory = "./storage"
    
    # Crear directorio de salida si no existe
    os.makedirs(output_directory, exist_ok=True)
    
    # Probar compresión con ZIP
    result = compress_backup(
        folders=folders_to_backup,
        output_path=output_directory,
        algorithm='zip',
        backup_name='test_backup'
    )
    
    print(f"Compresión completada:")
    print(f"- Archivo: {result['output_file']}")
    print(f"- Archivos procesados: {result['successful_files']}/{result['total_files']}")
    print(f"- Tamaño original: {result['original_size']:,} bytes")
    print(f"- Tamaño comprimido: {result['compressed_size']:,} bytes")
    print(f"- Ratio de compresión: {result['compression_ratio']:.2%}")
    print(f"- Tiempo de procesamiento: {result['processing_time']:.2f} segundos")