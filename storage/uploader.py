import os
from storage.cloud import authenticate

def upload_backup(file_path: str, filename_on_drive: str = None):
    """
    Upload a file to Google Drive.
    
    Args:
        file_path (str): Path to the file to upload
        filename_on_drive (str, optional): Name to use on Google Drive. Defaults to original filename.
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        # Get filename if not specified
        if not filename_on_drive:
            filename_on_drive = os.path.basename(file_path)

        # Authenticate and get drive instance
        drive = authenticate()

        # Create drive file instance
        file_drive = drive.CreateFile({'title': filename_on_drive})
        
        # Set content and upload
        file_drive.SetContentFile(file_path)
        file_drive.Upload()

        print(f"✓ Archivo '{filename_on_drive}' subido exitosamente a Google Drive")
        return True

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error al subir el archivo: {str(e)}")
        return False
