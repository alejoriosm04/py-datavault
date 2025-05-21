import os
from .cloud import authenticate

def upload_backup(file_path: str, filename_on_drive: str = None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    drive = authenticate()
    file_drive = drive.CreateFile({'title': filename_on_drive or os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"✅ Archivo '{file_path}' subido a Google Drive como '{file_drive['title']}'")
