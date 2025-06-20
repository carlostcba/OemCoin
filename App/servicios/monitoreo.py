# Archivo: App/servicios/monitoreo.py
import threading
import time
from datetime import datetime, timezone

from utilidades.logger import logger
from utilidades.helpers import leer_precio_ficha
from servicios.mercado_pago import buscar_pagos, obtener_detalles
from controladores.pago_controller import guardar_ficha_virtual, registrar_pago_procesado, cargar_ids_procesados
from controladores.gpio_controller import GPIOController
from configuracion.settings import POLL_INTERVAL, PULSO_FICHA_DURACION

sistema_funcionando = True
precio_ficha_actual = leer_precio_ficha()
controlador_gpio = GPIOController()
lock = threading.Lock()

def bucle_monitoreo():
    pagos_procesados = cargar_ids_procesados()
    inicio = datetime.now(timezone.utc)

    logger.info("[SERVICIO] Iniciando bucle de monitoreo de pagos...")

    while sistema_funcionando:
        try:
            pagos = buscar_pagos()

            for pago in pagos:
                if (pago.get("status") == "approved" and 
                    pago["id"] not in pagos_procesados and
                    pago.get("external_reference", "").startswith("LAV-")):

                    fecha_pago_str = pago.get("date_created")
                    fecha_pago = datetime.fromisoformat(fecha_pago_str.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
                    if fecha_pago < inicio.replace(tzinfo=None):
                        logger.info(f"[INFO] Ignorando pago anterior al arranque: {pago['id']}")
                        continue

                    detalles = obtener_detalles(pago["id"])
                    if detalles:
                        logger.info(f"[PAGO] Nuevo pago detectado: {pago['id']} - ${pago.get('transaction_amount')}")
                        if guardar_ficha_virtual(detalles):
                            registrar_pago_procesado(pago["id"], detalles["date_created"])
                            pagos_procesados.add(pago["id"])
                            activar_ficha_virtual()

            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"[ERROR] en bucle de monitoreo: {e}")
            time.sleep(POLL_INTERVAL)

def activar_ficha_virtual():
    logger.info("[GPIO] Simulando inserción de ficha virtual")
    controlador_gpio.activar(controlador_gpio.prod.pin.number, PULSO_FICHA_DURACION)
