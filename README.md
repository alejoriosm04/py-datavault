# Py-DataVault

A secure, parallel backup system with compression, encryption, and cloud support. Project for the seventh-semester course "Operating Systems" (ST0257) taught at EAFIT University.

## Setup

### 1. Dependencies
This project relies on several Python libraries. You can install them via pip using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Make sure you have `click` and `PyDrive2` among other dependencies listed in `requirements.txt`.

### 2. Authentication (for Cloud Backups)
To allow the application to access your Google Drive for cloud backups, you need to provide authentication credentials.

*   **`secrets/mycreds.txt`**: This file stores your Google Drive API credentials.
    *   The first time you attempt a cloud upload, the script will attempt to open a web browser for you to authenticate with your Google Account. Follow the on-screen instructions.
    *   After successful authentication, `mycreds.txt` will be created or updated in the `secrets/` directory.
    *   **Important**: Ensure the `secrets` directory exists at the root of your project.

**Recommended Directory Structure:**
```
py-datavault/
├── interface/
│   └── cli.py
├── secrets/
│   └── mycreds.txt
├── storage/
│   ├── cloud.py
│   ├── uploader.py
│   └── local.py
├── main.py
└── README.md
└── requirements.txt
```

## Usage

This project uses a command-line interface (CLI) to manage backups. You will interact with it via `main.py`.

### General Commands

*   **Help**: To see all available commands and their options:
    ```bash
    python main.py --help
    ```

### 1. Backing Up to the Cloud (Google Drive)

*   **Command**: `upload-cloud`
*   **Description**: Uploads a specified backup file to your Google Drive.
*   **Usage**:
    ```bash
    python main.py upload-cloud
    ```
    The CLI will prompt you for the path to the backup file.
    Alternatively, you can provide the path directly using the `--ruta` option:
    ```bash
    python main.py upload-cloud --ruta path/to/your/backupfile.zip
    ```

### 2. Copying Backup to an External Drive

*   **Command**: `copy-external`
*   **Description**: Copies a specified backup file to a local directory (e.g., an external hard drive).
*   **Usage**:
    ```bash
    python main.py copy-external
    ```
    The CLI will prompt you for the path to the backup file and the destination path on your external drive.
    Alternatively, you can provide these paths directly:
    ```bash
    python main.py copy-external --ruta-backup path/to/your/backupfile.zip --ruta-destino /media/my_external_drive/backups/
    ```

## Code Overview

*   **`main.py`**:
    *   The main entry point for the application. It imports and runs the CLI defined in `interface/cli.py`.

*   **`interface/cli.py`**:
    *   Defines the command-line interface structure using the `click` library.
    *   Contains commands like `upload-cloud` and `copy-external`.
    *   Handles user input, option parsing, and calls the appropriate functions from the `storage` module.

*   **`storage/` (Directory)**: Contains modules responsible for different storage operations.
    *   **`storage/cloud.py`**:
        *   `authenticate()`: Handles the Google Drive authentication process. It loads credentials from `secrets/mycreds.txt`, refreshes them if expired, or initiates a new authentication flow if necessary. Ensures `access_type='offline'` for refresh tokens.
    *   **`storage/uploader.py`**:
        *   `upload_backup(file_path: str, filename_on_drive: str = None)`: Uploads a file to Google Drive. It uses `authenticate()` from `storage.cloud`. `filename_on_drive` is an optional parameter to specify a different name for the file on Google Drive.
    *   **`storage/local.py`**:
        *   `copy_to_local_drive(source_file_path: str, destination_directory_path: str)`: Copies a file from a source path to a local destination directory. Raises errors for invalid paths or other copy issues.

*   **`secrets/` (Directory)**:
    *   Intended to store sensitive information like `mycreds.txt` (Google Drive API credentials). This directory should be included in your `.gitignore` file if you are using version control.

---

Happy Backupping! 🚀
