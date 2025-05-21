import os
import shutil

def copy_to_local_drive(source_file_path: str, destination_directory_path: str):
    if not os.path.exists(source_file_path):
        raise FileNotFoundError(f"Error: El archivo de backup {source_file_path} no existe.")
    
    if not os.path.isdir(destination_directory_path):
        raise NotADirectoryError(f"Error: El directorio de destino {destination_directory_path} no es válido o no es accesible.")

    try:
        file_name = os.path.basename(source_file_path)
        full_destination_path = os.path.join(destination_directory_path, file_name)
        shutil.copy2(source_file_path, full_destination_path)
        return full_destination_path
    except Exception as e:
        raise Exception(f"Error al copiar {source_file_path} a {destination_directory_path}: {e}") 
