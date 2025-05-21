import click
import os
from storage.uploader import upload_backup
from storage.local import copy_to_local_drive


@click.group()
def cli():
    pass

@cli.command()
@click.option('--ruta', prompt='Ruta del archivo de backup', help='La ruta al archivo que se va a subir a la nube.')
def upload_cloud(ruta):
    if not os.path.exists(ruta):
        click.echo(f"Error: El archivo {ruta} no existe.")
        return
    try:
        upload_backup(ruta)
        click.echo(f"Archivo {ruta} subido exitosamente a la nube.")
    except Exception as e:
        click.echo(f"Error al subir {ruta} a la nube: {e}")

@cli.command()
@click.option('--ruta-backup', prompt='Ruta del archivo de backup a copiar', help='La ruta al archivo de backup.')
@click.option('--ruta-destino', prompt='Ruta del disco externo', help='La ruta de destino en el disco duro externo.')
def copy_external(ruta_backup, ruta_destino):
    try:
        destino_completo = copy_to_local_drive(ruta_backup, ruta_destino)
        click.echo(f"Archivo {ruta_backup} copiado exitosamente a {destino_completo}.")
    except FileNotFoundError as e:
        click.echo(str(e))
    except NotADirectoryError as e:
        click.echo(str(e))
    except Exception as e:
        click.echo(str(e))
