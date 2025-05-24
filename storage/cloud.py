from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def authenticate():
    """
    Authenticate with Google Drive ensuring offline access.
    Returns a GoogleDrive instance if successful.
    """
    try:
        # Initialize GoogleAuth
        gauth = GoogleAuth()
        
        # Try to load saved client credentials
        gauth.LoadCredentialsFile("secrets/mycreds.txt")
        
        if gauth.credentials is None:
            # Authenticate if nothing stored
            gauth.GetFlow()
            gauth.flow.params.update({'access_type': 'offline'})
            gauth.flow.params.update({'approval_prompt': 'force'})
            
            # Create local webserver and handle authentication
            gauth.LocalWebserverAuth()
            
        elif gauth.access_token_expired:
            # Refresh them if expired
            try:
                gauth.Refresh()
            except Exception as e:
                print(f"Error refreshing token: {str(e)}")
                # If refresh fails, re-authenticate
                gauth.GetFlow()
                gauth.flow.params.update({'access_type': 'offline'})
                gauth.flow.params.update({'approval_prompt': 'force'})
                gauth.LocalWebserverAuth()
        
        # Save the current credentials
        gauth.SaveCredentialsFile("secrets/mycreds.txt")
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        # Si hay un error, eliminamos las credenciales existentes y reintentamos
        if os.path.exists("secrets/mycreds.txt"):
            os.remove("secrets/mycreds.txt")
        raise Exception("Error en la autenticación. Por favor, reintente el proceso.")
