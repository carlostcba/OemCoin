# Archivo: App/interfaz/display.py
import time
from utilidades.logger import logger
from configuracion.settings import PRECIO_DEFAULT
from utilidades.helpers import leer_precio_ficha
from servicios.mercado_pago import generar_preferencia
from configuracion.settings import QR_TEMP_PATH
import qrcode

def mostrar_qr_terminal():
    precio = leer_precio_ficha()
    qr_url, _ = generar_preferencia(precio)
    if qr_url:
        qr = qrcode.make(qr_url)
        qr.save(QR_TEMP_PATH)
        logger.info(f"[QR] Código QR generado y guardado en {QR_TEMP_PATH}")
    else:
        logger.error("[QR] No se pudo generar el código QR")

def loop_display():
    while True:
        mostrar_qr_terminal()
        logger.info("[DISPLAY] Esperando pago...")
        time.sleep(30)
