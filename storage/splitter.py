import os
import math
import dask
import click
from dask import delayed

def limpiar_ruta(path):
    return path.encode('ascii', 'ignore').decode().strip()

def calculate_fragmentation(file_path, fragment_size_mb):
    file_path = limpiar_ruta(file_path)
    fragment_size = fragment_size_mb * 1024 * 1024  
    file_size = os.path.getsize(file_path)
    total_fragments = math.ceil(file_size / fragment_size)

    click.secho(f"[INFO] Tamaño del archivo: {file_size} bytes", fg="cyan")
    click.secho(f"[INFO] Tamaño de cada fragmento: {fragment_size} bytes", fg="cyan")
    click.secho(f"[INFO] Total de fragmentos a crear: {total_fragments}", fg="cyan")

    return fragment_size, total_fragments

@delayed
def write_fragment(source_path, start, size, output_path):
    source_path = limpiar_ruta(source_path)
    output_path = limpiar_ruta(output_path)
    click.secho(f"[FRAGMENTANDO] Escribiendo fragmento: {output_path}", fg="yellow")
    with open(source_path, 'rb') as f:
        f.seek(start)
        data = f.read(size)
        with open(output_path, 'wb') as out:
            out.write(data)
    return output_path

def limpiar_usb(usb_paths):
    click.secho("[LIMPIEZA] Verificando y eliminando fragmentos previos...", fg="magenta")
    for ruta in usb_paths:
        ruta = limpiar_ruta(ruta)
        if os.path.exists(ruta):
            archivos = os.listdir(ruta)
            fragmentos = [f for f in archivos if ".part" in f]
            if not fragmentos:
                click.secho(f" - {ruta} ya estaba limpia.", fg="cyan")
            for f in fragmentos:
                path_completo = os.path.join(ruta, f)
                os.remove(path_completo)
                click.secho(f" - Eliminado: {path_completo}", fg="red")
        else:
            click.secho(f" - Advertencia: Ruta '{ruta}' no existe", fg="yellow")

def split_and_save_parallel(file_path, fragment_size_mb, usb_paths):
    file_path = limpiar_ruta(file_path)
    usb_paths = [limpiar_ruta(p) for p in usb_paths]
    limpiar_usb(usb_paths)

    click.secho(f"\n[INICIO] Fragmentando el archivo: {file_path}", fg="blue", bold=True)
    fragment_size, total_fragments = calculate_fragmentation(file_path, fragment_size_mb)
    tasks = []

    for i in range(total_fragments):
        start = i * fragment_size
        usb_index = i % len(usb_paths)
        fragment_name = f"{os.path.basename(file_path)}.part{i:03}"
        fragment_path = os.path.join(usb_paths[usb_index], fragment_name)
        click.secho(f"[ASIGNACIÓN] Fragmento {i} → {fragment_path}", fg="magenta")
        task = write_fragment(file_path, start, fragment_size, fragment_path)
        tasks.append(task)

    click.secho("\n[PROCESANDO] Ejecutando escritura en paralelo...", fg="yellow")
    results = dask.compute(*tasks)
    click.secho("[FINALIZADO] Todos los fragmentos fueron escritos exitosamente.\n", fg="green", bold=True)
    return results

@delayed
def read_fragment(fragment_path):
    fragment_path = limpiar_ruta(fragment_path)
    click.secho(f"[LEYENDO] Leyendo fragmento: {fragment_path}", fg="yellow")
    with open(fragment_path, 'rb') as f:
        return f.read()

def restore_from_fragments(usb_paths, output_path=None):
    usb_paths = [limpiar_ruta(p) for p in usb_paths]
    click.secho(f"\n[INICIO] Restaurando fragmentos desde: {usb_paths}", fg="blue", bold=True)
    fragment_paths = []

    for path in usb_paths:
        for f in os.listdir(path):
            if ".part" in f:
                full_path = os.path.join(path, f)
                fragment_paths.append(full_path)
                click.secho(f"[DETECTADO] Fragmento encontrado: {full_path}", fg="cyan")

    if not fragment_paths:
        click.secho("✗ No se encontraron fragmentos para restaurar.", fg="red")
        return None

    fragment_paths.sort(key=lambda x: int(x.split('.part')[-1]))

    first_fragment = os.path.basename(fragment_paths[0])
    nombre_base = first_fragment.split(".part")[0]

    if output_path is None:
        os.makedirs("restaured", exist_ok=True)
        output_path = os.path.join("restaured", nombre_base)

    click.secho(f"[INFO] Total de fragmentos a restaurar: {len(fragment_paths)}", fg="cyan")

    tasks = [read_fragment(p) for p in fragment_paths]
    chunks = dask.compute(*tasks)

    click.secho(f"[ESCRIBIENDO] Reconstruyendo archivo en: {output_path}", fg="yellow")
    with open(output_path, 'wb') as out:
        for chunk in chunks:
            out.write(chunk)

    click.secho(f"[FINALIZADO] Archivo restaurado exitosamente en: {output_path}\n", fg="green", bold=True)
    return output_path
