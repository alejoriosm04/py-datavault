from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def authenticate():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("secrets/mycreds.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("secrets/mycreds.txt")
    return GoogleDrive(gauth)

def upload_backup(file_path: str, filename_on_drive: str = None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    drive = authenticate()
    file_drive = drive.CreateFile({'title': filename_on_drive or os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"✅ Archivo '{file_path}' subido a Google Drive como '{file_drive['title']}'")
