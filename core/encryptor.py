import os
import base64
import secrets
import logging
from typing import Tuple, Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime
import dask
import dask.bag as db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Encryptor:
    """
    Clase para manejar la encriptación AES-256 de archivos de backup
    """
    
    def __init__(self):
        """Inicializa el encriptador"""
        self.algorithm = algorithms.AES
        self.key_length = 32  # 256 bits
        self.iv_length = 16   # 128 bits para AES
        self.salt_length = 16 # 128 bits para derivación de clave
        self.iterations = 100000  # Iteraciones PBKDF2
        
        logger.info("Encriptador AES-256 inicializado")
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Genera una clave AES-256 a partir de una contraseña usando PBKDF2
        
        Args:
            password: Contraseña del usuario
            salt: Salt para la derivación (si None, se genera uno nuevo)
            
        Returns:
            Tupla (clave_derivada, salt_usado)
        """
        if salt is None:
            salt = secrets.token_bytes(self.salt_length)
        
        # Configurar PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        
        # Derivar clave
        key = kdf.derive(password.encode('utf-8'))
        
        logger.info("Clave derivada exitosamente usando PBKDF2")
        return key, salt
    
    def generate_random_key(self) -> bytes:
        """
        Genera una clave AES-256 aleatoria
        
        Returns:
            Clave de 256 bits
        """
        key = secrets.token_bytes(self.key_length)
        logger.info("Clave aleatoria generada")
        return key
    
    def encrypt_data(self, data: bytes, password: str = None, key: bytes = None) -> Dict[str, Any]:
        """
        Encripta datos usando AES-256-CBC
        
        Args:
            data: Datos a encriptar
            password: Contraseña para derivar clave (opcional)
            key: Clave directa (opcional)
            
        Returns:
            Diccionario con datos encriptados y metadatos
        """
        if password is None and key is None:
            raise ValueError("Debe proporcionar una contraseña o una clave")
        
        if password is not None and key is not None:
            raise ValueError("Proporcione solo una contraseña O una clave, no ambas")
        
        start_time = datetime.now()
        
        # Obtener o generar clave
        if password:
            encryption_key, salt = self.generate_key_from_password(password)
        else:
            encryption_key = key
            salt = None
        
        # Generar IV aleatorio
        iv = secrets.token_bytes(self.iv_length)
        
        # Configurar cifrado
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Aplicar padding PKCS7
        padded_data = self._apply_pkcs7_padding(data)
        
        # Encriptar
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = {
            'encrypted_data': encrypted_data,
            'iv': iv,
            'salt': salt,
            'original_size': len(data),
            'encrypted_size': len(encrypted_data),
            'processing_time': processing_time,
            'algorithm': 'AES-256-CBC',
            'success': True
        }
        
        logger.info(f"Datos encriptados exitosamente en {processing_time:.2f}s")
        return result
    
    def decrypt_data(self, encrypted_data: bytes, iv: bytes, password: str = None, 
                    key: bytes = None, salt: bytes = None) -> Dict[str, Any]:
        """
        Desencripta datos usando AES-256-CBC
        
        Args:
            encrypted_data: Datos encriptados
            iv: Vector de inicialización usado en la encriptación
            password: Contraseña para derivar clave (opcional)
            key: Clave directa (opcional)
            salt: Salt usado para derivar la clave (requerido si se usa password)
            
        Returns:
            Diccionario con datos desencriptados y metadatos
        """
        if password is None and key is None:
            raise ValueError("Debe proporcionar una contraseña o una clave")
        
        if password is not None and key is not None:
            raise ValueError("Proporcione solo una contraseña O una clave, no ambas")
        
        start_time = datetime.now()
        
        # Obtener clave
        if password:
            if salt is None:
                raise ValueError("El salt es requerido para derivar la clave desde la contraseña")
            decryption_key, _ = self.generate_key_from_password(password, salt)
        else:
            decryption_key = key
        
        try:
            # Configurar descifrado
            cipher = Cipher(
                algorithms.AES(decryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Desencriptar
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remover padding PKCS7
            decrypted_data = self._remove_pkcs7_padding(padded_data)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = {
                'decrypted_data': decrypted_data,
                'decrypted_size': len(decrypted_data),
                'processing_time': processing_time,
                'success': True
            }
            
            logger.info(f"Datos desencriptados exitosamente en {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error durante la desencriptación: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def encrypt_file(self, input_path: str, output_path: str, password: str) -> Dict[str, Any]:
        """
        Encripta un archivo completo
        
        Args:
            input_path: Ruta del archivo a encriptar
            output_path: Ruta donde guardar el archivo encriptado
            password: Contraseña para la encriptación
            
        Returns:
            Información del resultado
        """
        try:
            # Leer archivo
            with open(input_path, 'rb') as f:
                file_data = f.read()
            
            # Encriptar datos
            encryption_result = self.encrypt_data(file_data, password=password)
            
            if not encryption_result['success']:
                return encryption_result
            
            # Crear estructura del archivo encriptado
            file_structure = self._create_encrypted_file_structure(encryption_result)
            
            # Guardar archivo encriptado
            with open(output_path, 'wb') as f:
                f.write(file_structure)
            
            result = {
                'input_file': input_path,
                'output_file': output_path,
                'original_size': encryption_result['original_size'],
                'encrypted_size': os.path.getsize(output_path),
                'processing_time': encryption_result['processing_time'],
                'algorithm': encryption_result['algorithm'],
                'success': True
            }
            
            logger.info(f"Archivo encriptado: {input_path} -> {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error encriptando archivo {input_path}: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def decrypt_file(self, input_path: str, output_path: str, password: str) -> Dict[str, Any]:
        """
        Desencripta un archivo completo
        
        Args:
            input_path: Ruta del archivo encriptado
            output_path: Ruta donde guardar el archivo desencriptado
            password: Contraseña para la desencriptación
            
        Returns:
            Información del resultado
        """
        try:
            # Leer archivo encriptado
            with open(input_path, 'rb') as f:
                encrypted_file_data = f.read()
            
            # Extraer estructura del archivo
            file_info = self._parse_encrypted_file_structure(encrypted_file_data)
            
            # Desencriptar datos
            decryption_result = self.decrypt_data(
                encrypted_data=file_info['encrypted_data'],
                iv=file_info['iv'],
                password=password,
                salt=file_info['salt']
            )
            
            if not decryption_result['success']:
                return decryption_result
            
            # Guardar archivo desencriptado
            with open(output_path, 'wb') as f:
                f.write(decryption_result['decrypted_data'])
            
            result = {
                'input_file': input_path,
                'output_file': output_path,
                'decrypted_size': decryption_result['decrypted_size'],
                'processing_time': decryption_result['processing_time'],
                'success': True
            }
            
            logger.info(f"Archivo desencriptado: {input_path} -> {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error desencriptando archivo {input_path}: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _apply_pkcs7_padding(self, data: bytes) -> bytes:
        """Aplica padding PKCS7 a los datos"""
        block_size = 16  # AES block size
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _remove_pkcs7_padding(self, padded_data: bytes) -> bytes:
        """Remueve padding PKCS7 de los datos"""
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
    
    def _create_encrypted_file_structure(self, encryption_result: Dict[str, Any]) -> bytes:
        """
        Crea la estructura del archivo encriptado con metadatos
        
        Formato:
        [4 bytes: tamaño salt][salt][4 bytes: tamaño IV][IV][datos encriptados]
        """
        salt = encryption_result['salt']
        iv = encryption_result['iv']
        encrypted_data = encryption_result['encrypted_data']
        
        # Construir estructura
        structure = bytearray()
        
        # Tamaño y salt
        structure.extend(len(salt).to_bytes(4, 'big'))
        structure.extend(salt)
        
        # Tamaño y IV
        structure.extend(len(iv).to_bytes(4, 'big'))
        structure.extend(iv)
        
        # Datos encriptados
        structure.extend(encrypted_data)
        
        return bytes(structure)
    
    def _parse_encrypted_file_structure(self, file_data: bytes) -> Dict[str, Any]:
        """
        Parsea la estructura del archivo encriptado
        
        Returns:
            Diccionario con salt, IV y datos encriptados
        """
        offset = 0
        
        # Leer tamaño del salt
        salt_size = int.from_bytes(file_data[offset:offset+4], 'big')
        offset += 4
        
        # Leer salt
        salt = file_data[offset:offset+salt_size]
        offset += salt_size
        
        # Leer tamaño del IV
        iv_size = int.from_bytes(file_data[offset:offset+4], 'big')
        offset += 4
        
        # Leer IV
        iv = file_data[offset:offset+iv_size]
        offset += iv_size
        
        # Resto son datos encriptados
        encrypted_data = file_data[offset:]
        
        return {
            'salt': salt,
            'iv': iv,
            'encrypted_data': encrypted_data
        }


# Funciones de conveniencia
def encrypt_backup_file(input_path: str, output_path: str, password: str) -> Dict[str, Any]:
    """
    Función de conveniencia para encriptar un archivo de backup
    
    Args:
        input_path: Archivo a encriptar
        output_path: Archivo encriptado resultante
        password: Contraseña para la encriptación
        
    Returns:
        Información del resultado
    """
    encryptor = Encryptor()
    return encryptor.encrypt_file(input_path, output_path, password)


def decrypt_backup_file(input_path: str, output_path: str, password: str) -> Dict[str, Any]:
    """
    Función de conveniencia para desencriptar un archivo de backup
    
    Args:
        input_path: Archivo encriptado
        output_path: Archivo desencriptado resultante
        password: Contraseña para la desencriptación
        
    Returns:
        Información del resultado
    """
    encryptor = Encryptor()
    return encryptor.decrypt_file(input_path, output_path, password)


if __name__ == "__main__":
    # Ejemplo de uso
    test_data = b"Este es un archivo de prueba para encriptacion"
    password = "mi_password_super_seguro"
    
    # Crear encriptador
    encryptor = Encryptor()
    
    # Encriptar datos
    print("Encriptando datos...")
    encryption_result = encryptor.encrypt_data(test_data, password=password)
    print(f"- Tamaño original: {encryption_result['original_size']} bytes")
    print(f"- Tamaño encriptado: {encryption_result['encrypted_size']} bytes")
    print(f"- Tiempo: {encryption_result['processing_time']:.3f}s")
    
    # Desencriptar datos
    print("\nDesencriptando datos...")
    decryption_result = encryptor.decrypt_data(
        encrypted_data=encryption_result['encrypted_data'],
        iv=encryption_result['iv'],
        password=password,
        salt=encryption_result['salt']
    )
    
    if decryption_result['success']:
        print(f"- Datos recuperados: {decryption_result['decrypted_data'].decode('utf-8')}")
        print(f"- Tiempo: {decryption_result['processing_time']:.3f}s")
        print("✓ Encriptación/Desencriptación exitosa!")
    else:
        print(f"✗ Error: {decryption_result['error']}")

