import os
import shutil
import subprocess
import click
import time
from storage.cloud import authenticate
from storage.uploader import upload_backup

def setup_test_environment():
    """Set up the test environment with necessary directories and test files."""
    # Create required directories if they don't exist
    directories = [
        'backups', 
        'usb1', 
        'usb2', 
        'restaured', 
        'secrets',
        'backend_output',
        'backend_output/encrypted',
        'temp_backup'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Create a test file in backups directory
    test_file_path = os.path.join('backups', 'test_file.txt')
    with open(test_file_path, 'w') as f:
        f.write('This is a test file for backup process.')

    return test_file_path

def cleanup_test_environment():
    """Clean up test artifacts."""
    directories_to_clean = [
        'usb1', 
        'usb2', 
        'restaured',
        'backend_output/encrypted',
        'temp_backup'
    ]
    for directory in directories_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            os.makedirs(directory, exist_ok=True)

def verify_cloud_upload(file_name):
    """Verify if a file was uploaded to Google Drive."""
    try:
        print("Verificando subida a Google Drive...")
        # Authenticate with Google Drive
        drive = authenticate()
        
        # Search for the file in Google Drive
        query = f"title contains '{file_name}'"
        print(f"Buscando archivo con nombre: {file_name}")
        file_list = drive.ListFile({'q': query}).GetList()
        
        # Check if the file exists
        exists = len(file_list) > 0
        if exists:
            print(f"✓ Archivo '{file_name}' encontrado en Google Drive")
        else:
            print(f"✗ Archivo '{file_name}' no encontrado en Google Drive")
        return exists
    except Exception as e:
        print(f"✗ Error verificando subida a la nube: {str(e)}")
        print("  Asegúrese de que:")
        print("  1. El directorio 'secrets/' existe")
        print("  2. Tiene credenciales válidas en 'secrets/mycreds.txt'")
        print("  3. Tiene conexión a internet")
        return False

def test_full_backup_process():
    """Run a complete test of the backup system."""
    try:
        print("Setting up test environment...")
        test_file = setup_test_environment()
        
        print("Cleaning up previous test artifacts...")
        cleanup_test_environment()

        print("Starting full backup process test...")
        command = [
            'python', 'main.py', 'full-backup-process',
            '--folders', './backups',
            '--backup-name', 'test_backup',
            '--compression', 'zip',
            '--encrypt',
            '--password', 'test123',
            '--usb-paths', 'usb1,usb2',
            '--cloud'  # Agregamos la opción de subida a la nube
        ]
        
        # Run the command and capture output
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Print the complete output for debugging
        print("\nCommand Output:")
        print(result.stdout)
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)

        # Verify the results
        success = False
        
        # Check if backup file was created
        backup_exists = any(
            f.startswith('test_backup') 
            for f in os.listdir('backend_output/encrypted')
        )
        
        # Check if fragments were created in USB directories
        usb1_has_fragments = len(os.listdir('usb1')) > 0
        usb2_has_fragments = len(os.listdir('usb2')) > 0
        
        # Check if restored file exists
        restored_exists = len(os.listdir('restaured')) > 0

        # Verify cloud upload
        print("\nVerifying cloud upload...")
        # Pequeña espera para asegurar que la subida se complete
        time.sleep(5)
        cloud_upload_success = verify_cloud_upload('test_backup')

        if backup_exists and usb1_has_fragments and restored_exists and cloud_upload_success:
            success = True
            print("\n✅ Test completed successfully!")
            print("- Backup file created in backend_output/encrypted")
            print("- USB fragments created (1 fragment in usb1)")
            print("- File restored successfully")
            print("- Cloud upload verified successfully")
        else:
            print("\n❌ Test failed!")
            print(f"- Backup file created in backend_output/encrypted: {'✅' if backup_exists else '❌'}")
            print(f"- USB1 fragments: {'✅' if usb1_has_fragments else '❌'}")
            print(f"- USB2 fragments: {'✅' if usb2_has_fragments else '❌'} (expected to be empty due to file size)")
            print(f"- Restored file: {'✅' if restored_exists else '❌'}")
            print(f"- Cloud upload: {'✅' if cloud_upload_success else '❌'}")

        return success

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = test_full_backup_process()
        if not success:
            exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)