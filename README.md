# Py-DataVault

A secure, parallel backup system with compression, encryption, USB fragmentation, and cloud support. Project for the seventh-semester course "Operating Systems" (ST0257) taught at EAFIT University.

## Setup

### 1. Dependencies

This project relies on several Python libraries. You can install them via pip using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Make sure you have `click`, `dask`, and `PyDrive2` among other dependencies listed in `requirements.txt`.

### 2. Authentication (for Cloud Backups)

To allow the application to access your Google Drive for cloud backups, you need to provide authentication credentials.

* **`secrets/mycreds.txt`**: This file stores your Google Drive API credentials.

  * The first time you attempt a cloud upload, the script will attempt to open a web browser for you to authenticate with your Google Account. Follow the on-screen instructions.
  * After successful authentication, `mycreds.txt` will be created or updated in the `secrets/` directory.
  * **Important**: Ensure the `secrets` directory exists at the root of your project.

**Directory Structure:**

```
py-datavault/
├── interface/
│   └── cli.py
├── secrets/
│   └── mycreds.txt
├── storage/
│   ├── cloud.py
│   ├── uploader.py
│   ├── local.py
│   └── splitter.py
├── usb1/
├── usb2/
├── tests/
│   └── carpetica_prueba.zip
├── restaured/
├── main.py
├── README.md
└── requirements.txt
```

> ⬆️ If not present, you must create the `usb1`, `usb2`, `tests`, `restaured`, and `secrets` folders before running fragmentation or restoration tests.

---

## Usage

This project uses a command-line interface (CLI) to manage backups. You will interact with it via `main.py`.

### General Commands

* **Help**: To see all available commands and their options:

  ```bash
  python main.py --help
  ```

### 1. Backing Up to the Cloud (Google Drive)

* **Command**: `upload-cloud`
* **Description**: Uploads a specified backup file to your Google Drive.
* **Usage**:

  ```bash
  python main.py upload-cloud
  ```

  The CLI will prompt you for the path to the backup file.
  Alternatively, you can provide the path directly using the `--ruta` option:

  ```bash
  python main.py upload-cloud --ruta path/to/your/backupfile.zip
  ```

### 2. Copying Backup to an External Drive

* **Command**: `copy-external`
* **Description**: Copies a specified backup file to a local directory (e.g., an external hard drive).
* **Usage**:

  ```bash
  python main.py copy-external
  ```

  The CLI will prompt you for the path to the backup file and the destination path on your external drive.
  Alternatively, you can provide these paths directly:

  ```bash
  python main.py copy-external --ruta-backup path/to/your/backupfile.zip --ruta-destino /media/my_external_drive/backups/
  ```

### 3. Fragmenting a Backup File to USBs

* **Command**: `fragmentar-usb`
* **Description**: Splits a file into `.partXXX` chunks and distributes them across multiple USB paths.
* **Usage**:

  ```bash
  python main.py fragmentar-usb
  ```

  Prompts for:

  * The file path to fragment
  * Fragment size in MB
  * Comma-separated USB paths

  Example:

  ```bash
  python main.py fragmentar-usb --archivo tests/carpetica_prueba.zip --tamano-fragmento 1 --usb-paths usb1,usb2
  ```

### 4. Restoring a Backup from USBs

* **Command**: `restaurar-usb`
* **Description**: Reconstructs a backup file from `.partXXX` fragments found in USB directories.
* **Usage**:

  ```bash
  python main.py restaurar-usb
  ```

  Prompts for USB paths. The file is restored automatically to:

  ```
  restaured/<original_filename>
  ```

  Or:

  ```bash
  python main.py restaurar-usb --usb-paths usb1,usb2
  ```

### 5. Default Fragmentation and Restoration Test

* **Command**: `test-fragmentar-restaurar`
* **Description**: Runs an end-to-end test using `tests/carpetica_prueba.zip`, splits it into `usb1` and `usb2`, and restores it to `restaured/`.
* **Usage**:

  ```bash
  python main.py test-fragmentar-restaurar
  ```

---

## Code Overview

* **`main.py`**:

  * The main entry point for the application. It imports and runs the CLI defined in `interface/cli.py`.

* **`interface/cli.py`**:

  * Defines the command-line interface structure using the `click` library.
  * Contains commands like `upload-cloud`, `copy-external`, `fragmentar-usb`, and `restaurar-usb`.
  * Handles user input, option parsing, and calls the appropriate functions from the `storage` module.

* **`storage/` (Directory)**: Contains modules responsible for different storage operations.

  * **`storage/cloud.py`**:

    * `authenticate()`: Handles the Google Drive authentication process. It loads credentials from `secrets/mycreds.txt`, refreshes them if expired, or initiates a new authentication flow if necessary. Ensures `access_type='offline'` for refresh tokens.
  * **`storage/uploader.py`**:

    * `upload_backup(file_path: str, filename_on_drive: str = None)`: Uploads a file to Google Drive. It uses `authenticate()` from `storage.cloud`. `filename_on_drive` is an optional parameter to specify a different name for the file on Google Drive.
  * **`storage/local.py`**:

    * `copy_to_local_drive(source_file_path: str, destination_directory_path: str)`: Copies a file from a source path to a local destination directory. Raises errors for invalid paths or other copy issues.
  * **`storage/splitter.py`**:

    * `split_and_save_parallel(file_path, fragment_size_mb, usb_paths)`: Splits a file into `.partXXX` fragments and distributes them in round-robin fashion.
    * `restore_from_fragments(usb_paths, output_path=None)`: Reconstructs a file from USB `.partXXX` files and saves it to `restaured/`.
    * Automatically cleans up previous `.part` files before fragmenting.

* **`secrets/` (Directory)**:

  * Intended to store sensitive information like `mycreds.txt` (Google Drive API credentials). This directory should be included in your `.gitignore` file if you are using version control.

---

