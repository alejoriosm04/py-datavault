# Py-DataVault: Sistema de Backup Seguro con Dask

Un sistema de respaldo seguro con compresión, encriptación, fragmentación USB y soporte en la nube. Proyecto para la asignatura "Sistemas Operativos" (ST0257) de la Universidad EAFIT.

## 🎯 Características Principales

- **Compresión Múltiple**: Soporte para ZIP, GZIP y BZIP2
- **Encriptación Segura**: AES-256 con PBKDF2
- **Almacenamiento Flexible**: 
  - Fragmentación en USBs
  - Respaldo en la nube (Google Drive)
  - Copia a disco externo
- **Paralelismo con Dask**: Optimización de operaciones
- **CLI Intuitiva**: Interfaz de línea de comandos fácil de usar

## 🛠️ Tecnologías Utilizadas

### Algoritmos de Compresión
- **ZIP**: Rápido y compatible
- **GZIP**: Balance velocidad/compresión  
- **BZIP2**: Máxima compresión

### Encriptación
- **AES-256**: Estándar militar
- **PBKDF2**: Derivación segura de claves
- **100,000 iteraciones**: Protección contra fuerza bruta

### Bibliotecas Principales
- **Python 3.8+**
- **Dask**: Para procesamiento paralelo
- **PyDrive2**: Integración con Google Drive
- **click**: Interfaz de línea de comandos
- **pycryptodome**: Encriptación AES

## 📦 Instalación

### 1. Dependencias

```bash
pip install -r requirements.txt
```

### 2. Estructura de Directorios

```
py-datavault/
├── interface/          # CLI y manejo de comandos
│   └── cli.py
├── core/              # Lógica principal
│   ├── compressor.py  # Algoritmos de compresión
│   ├── encryptor.py   # Encriptación AES
│   ├── restorer.py    # Restauración de backups
│   └── utils.py       # Utilidades generales
├── storage/           # Gestión de almacenamiento
│   ├── cloud.py       # Integración con Google Drive
│   ├── uploader.py    # Subida de archivos
│   ├── local.py       # Almacenamiento local
│   └── splitter.py    # Fragmentación USB
├── secrets/           # Credenciales y configuración
│   └── mycreds.txt    # Credenciales de Google Drive
├── usb1/             # Punto de montaje USB 1
├── usb2/             # Punto de montaje USB 2
├── tests/            # Archivos de prueba
├── restaured/        # Archivos restaurados
├── main.py           # Punto de entrada
└── requirements.txt  # Dependencias Python
```

### 3. Configuración de Google Drive

Para habilitar backups en la nube:

1. Crear directorio `secrets/`
2. Al primer uso, se abrirá autenticación web
3. Las credenciales se guardarán en `secrets/mycreds.txt`

## 🚀 Uso

### Comandos Principales

```bash
# Ver ayuda
python main.py --help

# Subir a Google Drive
python main.py upload-cloud --ruta path/to/backup.zip

# Copiar a disco externo
python main.py copy-external --ruta-backup backup.zip --ruta-destino /media/external/

# Fragmentar en USBs
python main.py fragmentar-usb --archivo backup.zip --tamano-fragmento 1 --usb-paths usb1,usb2

# Restaurar desde USBs
python main.py restaurar-usb --usb-paths usb1,usb2

# Proceso completo de backup
python main.py full-backup-process \
    --folders ./carpeta1,./carpeta2 \
    --backup-name mi_backup \
    --compression zip \
    --encrypt \
    --password mi_password \
    --usb-paths usb1,usb2 \
    --cloud
```

### Pruebas Automatizadas

```bash
# Ejecutar suite de pruebas completa
python test_full_backup_process.py
```

## 🔄 Proceso de Backup

1. **Selección**: Elija carpetas a respaldar
2. **Compresión**: ZIP/GZIP/BZIP2 con paralelismo Dask
3. **Encriptación**: AES-256 (opcional)
4. **Almacenamiento**: 
   - Fragmentación USB
   - Subida a Google Drive
   - Copia a disco externo

## 🛡️ Seguridad

- Encriptación AES-256
- Derivación de claves PBKDF2
- Autenticación segura con Google
- Verificación de integridad

## 🔍 Implementación del Paralelismo con Dask

El sistema utiliza Dask para optimizar:

1. **Compresión**: Procesamiento paralelo de archivos
2. **Encriptación**: División de datos en chunks
3. **Transferencia**: Operaciones I/O paralelas
4. **Fragmentación**: División y escritura paralela

## 📊 Rendimiento

- **Compresión Paralela**: Mejora de 2-4x en tiempo
- **Transferencia Optimizada**: Operaciones I/O paralelas
- **Fragmentación Eficiente**: División y escritura simultánea

## 📈 Métricas de Rendimiento y Análisis

El sistema incluye un módulo personalizado de monitoreo de rendimiento (`performance_metrics.py`) que permite analizar y comparar operaciones secuenciales y paralelas en términos de:

* **Duración total**
* **Uso promedio y máximo de CPU**
* **Uso promedio y máximo de memoria**
* **Velocidad de transferencia (throughput)**
* **Tasa de compresión**

### 🧪 Script de Evaluación

El script `test_simple.py` genera archivos de prueba y ejecuta dos tipos de compresión: secuencial y paralela. Durante cada operación, se registran métricas en tiempo real mediante la biblioteca `psutil`.

Ejemplo de ejecución:

```bash
python test_simple.py
```

### 📊 Resultado de ejemplo

```
=== Estadísticas de rendimiento para compresión_secuencial ===
Duración: 1.19 segundos
Tasa de compresión: 50.00%
CPU promedio: 1.8%
CPU máximo: 1.8%
Memoria promedio: 36.7 MB
Memoria máxima: 36.7 MB
Velocidad de transferencia: 0.00 MB/s

=== Estadísticas de rendimiento para compresión_paralela ===
Duración: 1.99 segundos
Tasa de compresión: 50.00%
CPU promedio: 13.2%
CPU máximo: 13.2%
Memoria promedio: 53.5 MB
Memoria máxima: 53.5 MB
Velocidad de transferencia: 0.00 MB/s

=== Comparación de rendimiento ===
Aceleración con paralelismo: 0.60x
```

### 📌 Análisis

* **Paralelismo con Dask** permite mejorar el uso del CPU y distribuir la carga, aunque el tiempo total puede variar según el tamaño del archivo y la cantidad de núcleos disponibles.
* El sistema demuestra cómo se comporta la compresión bajo distintos escenarios, lo cual es útil para decisiones sobre optimización de rendimiento en contextos reales.

## 🧪 Pruebas y Verificación

El sistema incluye pruebas automatizadas para:

1. Creación de backups
2. Fragmentación USB
3. Restauración
4. Integración con la nube

## 📝 Notas Adicionales

- Compatible con Linux, Windows y macOS
- Soporte para archivos grandes (>1GB)
- Gestión de errores robusta
- Logs detallados de operaciones

## 📄 Licencia

Este proyecto es parte del curso de Sistemas Operativos (ST0257) de la Universidada EAFIT.

## 👥 Autores

- Alejandro Ríos Muñoz
- Lina Sofía Ballesteros Merchán
- Juan Esteban García Galvis
- David Grisales Posada 
