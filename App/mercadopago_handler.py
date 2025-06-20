# -*- coding: utf-8 -*-
"""
Manejo de MercadoPago para el sistema de fichas virtuales
"""
import time
import logging
import mercadopago
from datetime import datetime
from config import ACCESS_TOKEN, LAVADERO_ID

class MercadoPagoHandler:
    def __init__(self):
        self.sdk = None
        self.inicializar_sdk()
    
    def inicializar_sdk(self):
        """Inicializa el SDK de MercadoPago"""
        try:
            self.sdk = mercadopago.SDK(ACCESS_TOKEN)
            logging.info("[OK] SDK MercadoPago inicializado para simulador de fichas")
        except Exception as e:
            logging.error(f"[ERROR] Error inicializando SDK: {e}")
            raise
    
    def generar_qr_ficha(self, precio):
        """Genera QR para compra de ficha virtual"""
        try:
            timestamp = int(time.time())
            external_reference = f"{LAVADERO_ID}-FICHA-{timestamp}"
            
            preference_data = {
                "items": [
                    {
                        "title": f"Ficha Virtual Lavadero {LAVADERO_ID}",
                        "description": "Ficha digital para lavado automático",
                        "quantity": 1,
                        "unit_price": round(precio, 2),
                        "currency_id": "ARS"
                    }
                ],
                "external_reference": external_reference,
                "statement_descriptor": f"LAVADERO-{LAVADERO_ID}",
                "payment_methods": {
                    "default_installments": 1,
                    "excluded_payment_types": [],
                    "excluded_payment_methods": []
                },
                "expires": True,
                "expiration_date_from": datetime.now().isoformat(),
                "expiration_date_to": datetime.fromtimestamp(
                    datetime.now().timestamp() + 1800  # 30 minutos para pagar
                ).isoformat(),
                "back_urls": {
                    "success": "https://www.mercadopago.com.ar/",
                    "failure": "https://www.mercadopago.com.ar/",
                    "pending": "https://www.mercadopago.com.ar/"
                },
                "auto_return": "approved"
            }
            
            logging.info(f"[INFO] Generando QR para ficha - Precio: ${precio}")
            preference_response = self.sdk.preference().create(preference_data)
            
            if preference_response["status"] == 201:
                preference = preference_response["response"]
                preference_id = preference["id"]
                init_point = preference["init_point"]
                
                logging.info(f"[OK] QR de ficha generado - ID: {preference_id}")
                return init_point, preference_id
            else:
                logging.error(f"[ERROR] Error creando preferencia de ficha: {preference_response}")
                return "https://www.mercadopago.com.ar", None
                
        except Exception as e:
            logging.error(f"[ERROR] Error generando QR de ficha: {e}")
            return "https://www.mercadopago.com.ar", None
    
    def consultar_pagos_fichas(self):
        """Consulta pagos de fichas virtuales usando solo conexiones de salida"""
        try:
            search_params = {
                "sort": "date_created",
                "criteria": "desc",
                "range": "date_created", 
                "begin_date": "NOW-1DAYS",
                "end_date": "NOW"
            }
            
            payments_response = self.sdk.payment().search(search_params)
            
            if payments_response["status"] == 200:
                results = payments_response["response"].get("results", [])
                
                # Buscar pagos aprobados de fichas de este lavadero
                for pago in results:
                    if (pago.get("status") == "approved" and 
                        (pago.get("external_reference") or "").startswith(f"{LAVADERO_ID}-FICHA")):
                        
                        return pago["id"], pago.get("transaction_amount", 0)
                
                return None, 0
            else:
                logging.warning(f"[WARN] Error en búsqueda de pagos: {payments_response}")
                return None, 0
                
        except Exception as e:
            logging.error(f"[ERROR] Error consultando pagos de fichas: {e}")
            return None, 0
    
    def obtener_detalles_pago_completo(self, payment_id):
        """Obtiene detalles completos del pago incluyendo información del pagador"""
        try:
            payment_response = self.sdk.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment_data = payment_response["response"]
                
                # Extraer información útil del pago
                pago_info = {
                    "id": payment_data.get("id"),
                    "status": payment_data.get("status"),
                    "status_detail": payment_data.get("status_detail"),
                    "transaction_amount": payment_data.get("transaction_amount", 0),
                    "currency_id": payment_data.get("currency_id", "ARS"),
                    "date_created": payment_data.get("date_created"),
                    "date_approved": payment_data.get("date_approved"),
                    "payment_method_id": payment_data.get("payment_method_id"),
                    "payment_type_id": payment_data.get("payment_type_id"),
                    "external_reference": payment_data.get("external_reference"),
                    "description": payment_data.get("description"),
                }
                
                # Información del pagador
                payer = payment_data.get("payer", {})
                pago_info["payer"] = {
                    "email": payer.get("email", "No disponible"),
                    "first_name": payer.get("first_name", ""),
                    "last_name": payer.get("last_name", ""),
                    "identification": payer.get("identification", {}),
                    "phone": payer.get("phone", {})
                }
                
                # Método de pago
                payment_method = payment_data.get("payment_method", {})
                pago_info["payment_method"] = {
                    "id": payment_method.get("id", ""),
                    "type": payment_method.get("type", ""),
                    "issuer_id": payment_method.get("issuer_id", "")
                }
                
                # Tarjeta (si aplica)
                card = payment_data.get("card", {})
                if card:
                    pago_info["card"] = {
                        "first_six_digits": card.get("first_six_digits", ""),
                        "last_four_digits": card.get("last_four_digits", ""),
                        "cardholder_name": card.get("cardholder", {}).get("name", "")
                    }
                
                return pago_info
            else:
                logging.error(f"[ERROR] Error obteniendo pago {payment_id}")
                return None
                
        except Exception as e:
            logging.error(f"[ERROR] Error obteniendo detalles: {e}")
            return None
    
    def test_conectividad_fichas(self):
        """Prueba la conectividad para sistema de fichas"""
        try:
            logging.info("[TEST] Probando conectividad para fichas...")
            
            test_data = {
                "items": [{"title": "Test Ficha", "quantity": 1, "unit_price": 1}]
            }
            
            response = self.sdk.preference().create(test_data)
            if response["status"] == 201:
                logging.info("[OK] Conectividad OK para fichas")
                return True
            else:
                logging.error(f"[ERROR] Error de conectividad: {response}")
                return False
                
        except Exception as e:
            logging.error(f"[ERROR] Error probando conectividad: {e}")
            return False

# Instancia global del manejador de MercadoPago
mp_handler = MercadoPagoHandler()