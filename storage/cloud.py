from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def authenticate():
    gauth = GoogleAuth()

    if 'oauth_flow_params' not in gauth.settings:
        gauth.settings['oauth_flow_params'] = {}
    gauth.settings['oauth_flow_params']['access_type'] = 'offline'
    gauth.settings['oauth_flow_params']['approval_prompt'] = 'force'

    gauth.LoadCredentialsFile("secrets/mycreds.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("secrets/mycreds.txt")
    return GoogleDrive(gauth)
