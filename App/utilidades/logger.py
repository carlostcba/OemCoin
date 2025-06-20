# Archivo: App/utilidades/logger.py
import logging
from configuracion.settings import LOGS_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("simulador_fichas")