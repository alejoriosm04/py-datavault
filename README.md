## py-datavault

### Project Structur

```
py-datavault/
├── core/
│   ├── compressor.py         # Compresión paralela con Dask
│   ├── encryptor.py          # Encriptación AES-256
│   ├── restorer.py           # Restauración completa
│   ├── utils.py              # Funciones comunes
│
├── storage/
│   ├── uploader.py           # Transferencia a disco, nube, USB
│   ├── cloud.py              # Integración con API Google Drive/Dropbox
│   ├── splitter.py           # Fragmentación de backup para USBs
│
├── interface/
│   ├── cli.py                # CLI interactivo con Typer o argparse
│
├── .env                      # Claves de nube / encriptación (usando dotenv)
├── requirements.txt
├── README.md
└── main.py
```
