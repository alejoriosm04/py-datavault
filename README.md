# Py-DataVault

A secure, parallel backup system with compression, encryption, and cloud support. Project for the seventh-semester course "Operating Systems" (ST0257) taught at EAFIT University.

## Setup

### 1. Dependencies
This project relies on the `PyDrive2` library. You can install it via pip:
```bash
pip install PyDrive2
```

### 2. Authentication
To allow the application to access your Google Drive, you need to provide authentication credentials.

*   **`mycreds.txt`**: This file stores your Google Drive API credentials.
    *   You should have received a `mycreds.txt` file.
    *   Place this file inside a directory named `secrets` at the root of the project. The path should be: `secrets/mycreds.txt`.
    *   **Important**: If `mycreds.txt` is not found or the credentials expire, the script will attempt to open a web browser for you to authenticate with your Google Account. Follow the on-screen instructions. After successful authentication, `mycreds.txt` will be created or updated in the `secrets/` directory.

**Directory Structure for Credentials:**
```
py-datavault/
├── secrets/
│   └── mycreds.txt
├── storage/
│   └── cloud.py
└── main.py
```

## Usage

### 1. Preparing Files for Backup
Place the files you want to back up in any location accessible by your system. For organizational purposes, you might want to create a dedicated `backups/` directory within the project, but this is not mandatory.

Example:
```
py-datavault/
├── backups/
│   └── my_important_document.txt
│   └── hola2.txt
├── secrets/
│   └── mycreds.txt
├── storage/
│   └── cloud.py
└── main.py
```

### 2. Configuring `main.py`
The `main.py` script is where you specify which file to upload.

Open `main.py` and modify the `ruta` variable to point to the local file you wish to upload.

```python
from storage.cloud import upload_backup

if __name__ == "__main__":
    # Modify this path to your target file
    ruta = "backups/hola2.txt"
    upload_backup(ruta) # Uploads with the same filename as the local file

    # To specify a different name on Google Drive:
    # upload_backup(ruta, filename_on_drive="my_backup_on_drive.txt")
```

### 3. Running the Script
Execute the `main.py` script from your terminal:
```bash
python main.py
```
Upon successful execution, you will see a confirmation message:
`✅ Archivo '[your_local_file_path]' subido a Google Drive como '[filename_on_drive]'`

## Code Overview

*   **`storage/cloud.py`**:
    *   `authenticate()`: Handles the Google Drive authentication process. It loads credentials from `secrets/mycreds.txt`, refreshes them if expired, or initiates a new authentication flow if necessary.
    *   `upload_backup(file_path: str, filename_on_drive: str = None)`:
        *   Takes the `file_path` (local path to the file) as a mandatory argument.
        *   Optionally, `filename_on_drive` can be provided to specify a different name for the file when it's saved on Google Drive. If not provided, the original filename is used.
        *   Raises a `FileNotFoundError` if the `file_path` does not exist.
        *   Authenticates using `authenticate()`, creates a new file on Google Drive, sets its content from the local file, and uploads it.

*   **`main.py`**:
    *   The main script to execute the backup process.
    *   Imports `upload_backup` from `storage.cloud`.
    *   Sets the `ruta` variable to the path of the file to be backed up.
    *   Calls `upload_backup()` to upload the specified file.

---

Happy Backupping! 🚀
