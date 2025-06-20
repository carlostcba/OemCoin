# Archivo: App/controladores/pago_controller.py
import json
import os
from datetime import datetime
from configuracion.settings import LOG_PATH, PAGOS_PROCESADOS_PATH, LAVADERO_ID, RELAY_PIN, PULSO_FICHA_DURACION
from utilidades.logger import logger

def cargar_ids_procesados():
    pagos = set()
    try:
        with open(PAGOS_PROCESADOS_PATH, "r") as f:
            for linea in f:
                partes = linea.strip().split()
                if partes:
                    pagos.add(partes[0])
    except FileNotFoundError:
        logger.info("[INFO] pagos_procesados.txt no existe, se creará uno nuevo.")
    return pagos

def registrar_pago_procesado(payment_id, fecha):
    try:
        with open(PAGOS_PROCESADOS_PATH, "a") as f:
            f.write(f"{payment_id} {fecha}\n")
    except Exception as e:
        logger.error(f"[ERROR] No se pudo registrar pago procesado: {e}")

def guardar_ficha_virtual(payment_details):
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        payment_id = payment_details["id"]
        archivo = os.path.join(LOG_PATH, f"{timestamp}_{payment_id}.json")

        data_ficha = {
            "timestamp_local": datetime.now().isoformat(),
            "lavadero_id": LAVADERO_ID,
            "tipo_servicio": "ficha_virtual",
            "sistema_control": "dispositivo_analogico_existente",
            "duracion_pulso_segundos": PULSO_FICHA_DURACION,
            "modo": "standalone_polling",
            "gpio_utilizado": RELAY_PIN,
            "payment_details": payment_details
        }

        with open(archivo, "w", encoding='utf-8') as f:
            json.dump(data_ficha, f, indent=2, ensure_ascii=False)

        logger.info(f"[OK] Ficha virtual registrada: {archivo}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Error guardando ficha: {e}")
        return False
