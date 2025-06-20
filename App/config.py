# -*- coding: utf-8 -*-
"""
Configuración del sistema de fichas virtuales
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Claves de MercadoPago
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Configuración de paths
APP_PATH = os.getenv("APP_PATH", "/home/oemspot/App")
LOG_PATH = os.path.join(APP_PATH, "pagos_fichas")
PRECIO_PATH = os.path.join(APP_PATH, "precio_ficha.txt")
LOGS_FILE = os.path.join(APP_PATH, "simulador_fichas.log")
QR_TEMP_PATH = os.path.join(APP_PATH, "qr_ficha.png")
PAGOS_PROCESADOS_PATH = os.path.join(APP_PATH, "pagos_procesados.txt")

# Configuración GPIO
RELAY_PRODUCCION = int(os.getenv("RELAY_PRODUCCION", "17"))
RELAY_AUXILIAR = int(os.getenv("RELAY_AUXILIAR", "27"))

# Configuración del sistema
PULSO_FICHA_DURACION = float(os.getenv("PULSO_FICHA_DURACION", "1.0"))
PRECIO_DEFAULT = float(os.getenv("PRECIO_DEFAULT", "1.0"))
LAVADERO_ID = os.getenv("LAVADERO_ID", "LAV-001")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "3"))

# Crear directorios necesarios
os.makedirs(APP_PATH, exist_ok=True)
os.makedirs(LOG_PATH, exist_ok=True)