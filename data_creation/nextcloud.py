import os
import shutil
from webdav3.client import Client
import getpass
 
def long_path(path):
    """
    Prepara la ruta para manejar rutas largas en Windows.
    """
    if os.name == 'nt':
        path = os.path.abspath(path)
        if not path.startswith('\\\\?\\'):
            path = '\\\\?\\' + path
    return path
 
def download_recursive(client, remote_path, local_path, error_count):
    # Asegurarse de que el directorio local actual existe
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    items = client.list(remote_path)
    print(f"Listing {remote_path}: {items}")  # Depuración
    remote_basename = os.path.basename(remote_path.rstrip('/'))
    for item in items:
        if item in ['.', '..']:
            continue
        print(f"Processing item: {item}")
        # Obtener el nombre base del item sin barras al final
        item_basename = os.path.basename(item.rstrip('/'))
        # Verificar si el item es el mismo que el directorio actual para evitar redundancias
        if item_basename == remote_basename:
            print(f"Skipping item {item} as it is the same as remote_path basename")
            continue
        # Construir la ruta remota del item
        remote_item_path = f"{remote_path.rstrip('/')}/{item.lstrip('/')}"
        print(f"Remote item path: {remote_item_path}")
        # Construir la ruta local del item
        # Reemplazar '/' por os.sep para manejar subdirectorios correctamente
        item_local = item.strip('/').replace('/', os.sep)
        local_item_path = os.path.join(local_path, item_local)
        # Preparar la ruta local para manejar rutas largas
        local_item_path = long_path(local_item_path)
        print(f"Local item path: {local_item_path}")
        if client.is_dir(remote_item_path):
            # Llamada recursiva con rutas actualizadas
            download_recursive(client, remote_item_path, local_item_path)
        else:
            # Asegurarse de que el directorio padre existe
            parent_dir = os.path.dirname(local_item_path)
            parent_dir = long_path(parent_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            print(f'Descargando archivo {remote_item_path} a {local_item_path}')
            try:
                client.download_sync(remote_path=remote_item_path, local_path=local_item_path)
            except Exception as e:
                error_count[0] += 1
                print(f"Error al descargar {remote_item_path}: {e}")
                
def move_eml_files_up(project_folder, error_count):
    # Buscar todos los archivos .eml dentro de project_folder
    eml_files = []
    for root, dirs, files in os.walk(project_folder):
        for file in files:
            if file.lower().endswith('.eml'):
                file_path = os.path.join(root, file)
                eml_files.append(file_path)
    # Mover todos los archivos .eml a project_folder
    for eml_file in eml_files:
        dest_file = os.path.join(project_folder, os.path.basename(eml_file))
        # Preparar las rutas para manejar rutas largas
        eml_file = long_path(eml_file)
        dest_file = long_path(dest_file)
        try:
            if not os.path.exists(dest_file):
                shutil.move(eml_file, dest_file)
            else:
                # Manejar archivos con nombres duplicados
                base, ext = os.path.splitext(os.path.basename(eml_file))
                counter = 1
                while True:
                    new_filename = f"{base}_{counter}{ext}"
                    dest_file = os.path.join(project_folder, new_filename)
                    dest_file = long_path(dest_file)
                    if not os.path.exists(dest_file):
                        shutil.move(eml_file, dest_file)
                        break
                    counter += 1
        except Exception as e:
            error_count[0] += 1
            print(f"Error al mover {eml_file} a {dest_file}: {e}")            

    # Eliminar todas las subcarpetas dentro de project_folder
    for item in os.listdir(project_folder):
        item_path = os.path.join(project_folder, item)
        item_path = long_path(item_path)
        if os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
            except Exception as e:
                error_count[0] += 1
                print(f"Error al eliminar la carpeta {item_path}: {e}")                
 
def main():
    # Configuración de conexión
    webdav_hostname = "https://cloud.alfatec.es/remote.php/dav"
    webdav_root = "/files/connecthink"
    nc_user = "connecthink"
    # Solicitar contraseña de forma segura
    nc_password = getpass.getpass("Introduce tu contraseña de Nextcloud: ")
 
    options = {
        'webdav_hostname': webdav_hostname,
        'webdav_root': webdav_root,
        'webdav_login':    nc_user,
        'webdav_password': nc_password
    }
 
    client = Client(options)

    # Contador de errores
    error_count = [0]  # Usamos una lista para modificar el contador dentro de funciones

    # --- Paso 1: Descargar la carpeta desde Nextcloud ---
    remote_dir = '/documentos_proyecto_IA'
    local_dir = os.path.abspath('documentos_proyecto_IA')  # Ruta más corta para evitar problemas de longitud
    print("Iniciando descarga de Nextcloud...")
    download_recursive(client, remote_dir, local_dir, error_count)
 
    # --- Paso 2: Reorganizar la estructura localmente ---
    project_root = local_dir
    for item in os.listdir(project_root):
        project_folder = os.path.join(project_root, item)
        project_folder = long_path(project_folder)
        if os.path.isdir(project_folder):
            print(f"Procesando carpeta del proyecto: {project_folder}")
            move_eml_files_up(project_folder)

    print(f"Proceso completado con {error_count[0]} errores.")


if __name__ == "__main__":
    main()