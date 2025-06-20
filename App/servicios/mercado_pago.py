# Archivo: App/servicios/mercado_pago.py
import mercadopago
from configuracion.settings import ACCESS_TOKEN, LAVADERO_ID
from utilidades.logger import logger
from datetime import datetime
import time

sdk = mercadopago.SDK(ACCESS_TOKEN)

def generar_preferencia(precio):
    try:
        timestamp = int(time.time())
        external_reference = f"{LAVADERO_ID}-FICHA-{timestamp}"

        preference_data = {
            "items": [
                {
                    "title": f"Ficha Virtual {LAVADERO_ID}",
                    "quantity": 1,
                    "unit_price": round(precio, 2),
                    "currency_id": "ARS"
                }
            ],
            "external_reference": external_reference,
            "expires": True,
            "expiration_date_from": datetime.now().isoformat(),
            "expiration_date_to": datetime.fromtimestamp(time.time() + 1800).isoformat(),
            "back_urls": {
                "success": "https://www.mercadopago.com.ar/",
                "failure": "https://www.mercadopago.com.ar/",
                "pending": "https://www.mercadopago.com.ar/"
            },
            "auto_return": "approved"
        }

        response = sdk.preference().create(preference_data)
        if response["status"] == 201:
            logger.info(f"[MP] Preferencia creada: {response['response']['id']}")
            return response["response"]["init_point"], response["response"]["id"]
        else:
            logger.error(f"[MP] Error al crear preferencia: {response}")
            return None, None

    except Exception as e:
        logger.error(f"[MP] Excepción generando preferencia: {e}")
        return None, None

def buscar_pagos():
    try:
        search_params = {
            "sort": "date_created",
            "criteria": "desc",
            "range": "date_created", 
            "begin_date": "NOW-1DAYS",
            "end_date": "NOW"
        }
        response = sdk.payment().search(search_params)
        if response["status"] == 200:
            return response["response"].get("results", [])
        else:
            logger.warning(f"[MP] Error buscando pagos: {response}")
            return []
    except Exception as e:
        logger.error(f"[MP] Excepción buscando pagos: {e}")
        return []

def obtener_detalles(payment_id):
    try:
        response = sdk.payment().get(payment_id)
        if response["status"] == 200:
            return response["response"]
        else:
            logger.error(f"[MP] Error al obtener detalles del pago {payment_id}")
            return None
    except Exception as e:
        logger.error(f"[MP] Excepción al obtener detalles de pago: {e}")
        return None