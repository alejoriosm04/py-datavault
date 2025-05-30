import click
import os
from storage.uploader import upload_backup
from storage.local import copy_to_local_drive
from storage.splitter import split_and_save_parallel, restore_from_fragments
from core.utils import BackupManager

CONTEXT_SETTINGS = dict(help_option_names=['--help'], max_content_width=120)

def print_banner():
    click.secho("\n╔════════════════════════════════════════════════════════════════╗", fg="cyan", bold=True)
    click.secho("║                    Py-DataVault CLI Tool                       ║", fg="cyan", bold=True)
    click.secho("║                  Secure Backup System                          ║", fg="cyan", bold=True)
    click.secho("╚════════════════════════════════════════════════════════════════╝\n", fg="cyan", bold=True)

class CustomCLI(click.Group):
    def format_help(self, ctx, formatter):
        print_banner()
        super().format_help(ctx, formatter)

    def format_commands(self, ctx, formatter):
        commands = self.list_commands(ctx)
        with formatter.section(click.style('Comandos disponibles:', fg='yellow', bold=True)):
            rows = []
            for cmd in commands:
                command = self.get_command(ctx, cmd)
                help_str = command.get_short_help_str().strip().split('.')[0]
                rows.append((click.style(cmd, fg='bright_blue'), click.style(help_str, fg='white')))
            formatter.write_dl(rows)

@click.group(cls=CustomCLI, context_settings=CONTEXT_SETTINGS)
def cli():
    pass

@cli.command()
@click.option('--ruta', prompt='Ruta del archivo de backup', help='La ruta al archivo que se va a subir a la nube.')
def upload_cloud(ruta):
    """Sube archivo a Google Drive."""
    click.secho("╭────────── SUBIDA A LA NUBE ──────────╮", fg="blue", bold=True)
    if not os.path.exists(ruta):
        click.secho(f"✗ Error: El archivo '{ruta}' no existe.", fg="red")
        return
    try:
        upload_backup(ruta)
        click.secho(f"✓ Archivo '{ruta}' subido exitosamente.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"✗ Error al subir a la nube: {e}", fg="red")

@cli.command()
@click.option('--ruta-backup', prompt='Ruta del archivo de backup a copiar', help='La ruta al archivo de backup.')
@click.option('--ruta-destino', prompt='Ruta del disco externo', help='La ruta de destino en el disco duro externo.')
def copy_external(ruta_backup, ruta_destino):
    """Copia backup a disco externo."""
    click.secho("╭─────── COPIA A DISCO EXTERNO ───────╮", fg="blue", bold=True)
    try:
        destino_completo = copy_to_local_drive(ruta_backup, ruta_destino)
        click.secho(f"✓ Copiado exitosamente a: {destino_completo}", fg="green", bold=True)
    except (FileNotFoundError, NotADirectoryError) as e:
        click.secho(f"✗ {str(e)}", fg="red")
    except Exception as e:
        click.secho(f"✗ Error inesperado: {e}", fg="red")

@cli.command()
@click.option('--archivo', prompt='Ruta del archivo de backup a fragmentar', help='Ruta del archivo que se va a fragmentar.')
@click.option('--tamano-fragmento', prompt='Tamaño de cada fragmento en MB', type=int, help='Tamaño del fragmento en MB.')
@click.option('--usb-paths', prompt='Rutas de las USB (separadas por coma)', help='Ej: usb1,usb2')
def fragmentar_usb(archivo, tamano_fragmento, usb_paths):
    """Fragmenta y distribuye en USBs."""
    click.secho("╭───────── FRAGMENTACIÓN EN USBs ─────────╮", fg="blue", bold=True)
    rutas_usb = usb_paths.split(',')
    try:
        resultados = split_and_save_parallel(archivo, tamano_fragmento, rutas_usb)
        click.secho("✓ Fragmentación completa:", fg="green", bold=True)
        for r in resultados:
            click.secho(f"  - {r}", fg="white")
    except Exception as e:
        click.secho(f"✗ Error al fragmentar: {e}", fg="red")

@cli.command()
@click.option('--usb-paths', prompt='Rutas de las USB (separadas por coma)', help='Ej: usb1,usb2')
def restaurar_usb(usb_paths):
    """Reconstruye archivo desde USBs en la carpeta 'restaured'."""
    click.secho("╭───────── RESTAURACIÓN DESDE USBs ─────────╮", fg="blue", bold=True)
    rutas_usb = usb_paths.split(',')
    try:
        archivo_final = restore_from_fragments(rutas_usb)
        if archivo_final:
            click.secho(f"✓ Archivo restaurado en: {archivo_final}", fg="green", bold=True)
    except Exception as e:
        click.secho(f"✗ Error al restaurar: {e}", fg="red")

@cli.command()
def test_fragmentar_restaurar():
    """Prueba completa con ZIP de ejemplo."""
    click.secho("╭───── PRUEBA COMPLETA AUTOMÁTICA ─────╮", fg="yellow", bold=True)
    archivo_test = os.path.join("tests", "carpetica_prueba.zip")
    salida = os.path.join("restaured", "carpetica_restaurada.zip")
    rutas_usb = ["usb1", "usb2"]
    tamano_fragmento = 1

    try:
        click.secho("1. Fragmentando archivo de prueba...", fg="cyan")
        split_and_save_parallel(archivo_test, tamano_fragmento, rutas_usb)
        click.secho("2. Restaurando desde fragmentos...", fg="cyan")
        restore_from_fragments(rutas_usb, salida)
        click.secho(f"\n✓ Archivo restaurado en: {salida}", fg="green", bold=True)
    except Exception as e:
        click.secho(f"✗ Error durante la prueba: {e}", fg="red")

@cli.command()
@click.option('--folders', required=True, help='Comma-separated list of folders to backup.')
@click.option('--backup-name', required=True, help='Name of the backup file.')
@click.option('--compression', default='zip', help='Compression algorithm: zip, gzip, or bzip2.')
@click.option('--encrypt', is_flag=True, help='Encrypt the backup.')
@click.option('--password', default=None, help='Password for encryption.')
@click.option('--usb-paths', required=True, help='Comma-separated USB paths for fragmentation.')
@click.option('--cloud', is_flag=True, help='Upload to cloud after backup.')
def full_backup_process(folders, backup_name, compression, encrypt, password, usb_paths, cloud):
    """Execute a complete backup process including fragmentation and optional cloud upload."""
    click.secho("╭───────── PROCESO COMPLETO DE BACKUP ─────────╮", fg="blue", bold=True)
    
    try:
        # Create backup
        click.echo("1. Creating backup...")
        manager = BackupManager()
        result = manager.create_backup(
            folders=folders.split(','),
            backup_name=backup_name,
            compression_algorithm=compression,
            encrypt=encrypt,
            password=password
        )
        if not result['success']:
            click.secho("✗ Backup creation failed.", fg="red")
            return
        click.secho("✓ Backup created successfully", fg="green")

        # Fragment backup
        click.echo("\n2. Fragmenting backup...")
        split_and_save_parallel(result['backup_file'], 1, usb_paths.split(','))
        click.secho("✓ Backup fragmented successfully", fg="green")

        # Restore backup
        click.echo("\n3. Restoring from fragments...")
        restored_file = restore_from_fragments(usb_paths.split(','))
        if restored_file:
            click.secho(f"✓ Backup restored successfully to: {restored_file}", fg="green")

        # Upload to cloud
        if cloud:
            click.echo("\n4. Uploading to cloud...")
            upload_backup(result['backup_file'])
            click.secho("✓ Backup uploaded to cloud successfully", fg="green")

        click.secho("\n✓ Full backup process completed successfully.", fg="green", bold=True)

    except Exception as e:
        click.secho(f"\n✗ Error during backup process: {str(e)}", fg="red")
        raise
