# 📦 SISTEMA DE BACKUP SEGURO
**Versión:** 1.0.0   

---

## 🛠️ **QUÉ UTILIZA**

### **Algoritmos de Compresión:**
- **ZIP** - Rápido y compatible
- **GZIP** - Balance velocidad/compresión  
- **BZIP2** - Máxima compresión

### **Encriptación:**
- **AES-256** - Estándar militar
- **PBKDF2** - Derivación segura de claves
- **100,000 iteraciones** - Protección contra fuerza bruta

### **Tecnologías:**
- **Python 3.8+**
- **Librerías estándar:** zipfile, tarfile, os, shutil
- **Librerías adicionales:** pycryptodome

---

## ⚙️ **CÓMO FUNCIONA**

### **Flujo Simple:**
```
1. Tienes archivos en backups/
2. Ejecutas el sistema
3. Elige algoritmo (zip/gzip/bzip2)
4. Opcionalmente encripta
5. Guarda automáticamente en backend_output/
```

### **Organización Automática:**
```
backend_output/
├── compressed/zip/      # Backups ZIP
├── compressed/gzip/     # Backups GZIP  
├── compressed/bzip2/    # Backups BZIP2
├── encrypted/           # Backups encriptados
├── restored/            # Archivos restaurados
└── tests/              # Backups de prueba
```

---

## 🔄 **CICLO COMPLETO**

### **PASO 1: Preparación**
```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Poner archivos en backups/
# Ya tienes: imagen.jpg, proyectoprueba.docx, test_file1.txt, etc.
```

### **PASO 2: Crear Backup**
```python
from core.utils import BackupManager

manager = BackupManager()

# Backup básico
resultado = manager.create_backup(
    folders=["./backups"],
    backup_name="mi_backup",
    compression_algorithm='zip'  # o 'gzip' o 'bzip2'
)

# Backup encriptado
resultado = manager.create_backup(
    folders=["./backups"],
    backup_name="backup_seguro", 
    compression_algorithm='gzip',
    encrypt=True,
    password="mi_contraseña"
)
```

### **PASO 3: Verificar Resultado**
```python
if resultado['success']:
    print(f"✅ Backup creado: {resultado['backup_file']}")
    print(f"📊 Compresión: {resultado['compression_ratio']:.2%}")
    print(f"⏱️ Tiempo: {resultado['compression_time']:.2f}s")
```

### **PASO 4: Restaurar**
```python
# Restaurar backup normal
resultado = manager.restore_backup("backend_output/compressed/zip/mi_backup.zip")

# Restaurar backup encriptado
resultado = manager.restore_backup(
    "backend_output/encrypted/backup_seguro.tar.gz.encrypted",
    password="mi_contraseña"
)
```

---

## 🧪 **CÓMO PROBARLO**

### **Opción 1: Script de Prueba Automática (RECOMENDADO)**

**¡Ya está creado! Usa el script `test_sistema_completo.py`**

```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Ejecutar script de prueba completa
python test_sistema_completo.py
```

**Este script hace TODO automáticamente:**
- ✅ Verifica archivos en `backups/`
- ✅ Prueba backup ZIP, GZIP y BZIP2
- ✅ Prueba backup encriptado con contraseña
- ✅ Prueba restauración normal y encriptada
- ✅ Compara rendimiento de algoritmos
- ✅ Muestra estructura de directorios creada
- ✅ Da resumen completo de funcionamiento

**Resultado esperado:**
```
🎯 SISTEMA FUNCIONANDO CORRECTAMENTE ✅
```

### **Opción 2: Prueba Manual Paso a Paso**

Si prefieres probar manualmente cada componente:

#### **1. Verificar que tienes archivos:**
```bash
dir backups
# Debes ver: imagen.jpg, proyectoprueba.docx, test_file1.txt, etc.
```

#### **2. Probar backup ZIP:**
```python
from core.utils import BackupManager
manager = BackupManager()

resultado = manager.create_backup(
    folders=["./backups"],
    backup_name="test_zip",
    compression_algorithm='zip'
)

print(f"Resultado: {resultado['success']}")
print(f"Archivo: {resultado['backup_file']}")
```

#### **3. Probar backup GZIP:**
```python
resultado = manager.create_backup(
    folders=["./backups"],
    backup_name="test_gzip", 
    compression_algorithm='gzip'
)
```

#### **4. Probar backup encriptado:**
```python
resultado = manager.create_backup(
    folders=["./backups"],
    backup_name="test_encrypted",
    compression_algorithm='gzip',
    encrypt=True,
    password="test123"
)
```

#### **5. Verificar estructura creada:**
```bash
dir backend_output /s
# Debes ver los directorios y archivos organizados
```

#### **6. Probar restauración:**
```python
# Restaurar el último backup
resultado = manager.restore_backup(
    "backend_output/compressed/zip/test_zip.zip"
)

print(f"Restaurado en: {resultado['restore_directory']}")
```

---