# -*- coding: utf-8 -*-
"""
Monitor de pagos para el sistema de fichas virtuales
"""
import time
import logging
import threading
from datetime import datetime, timezone
from config import POLL_INTERVAL
from mercadopago_handler import mp_handler
from file_manager import file_manager
from hardware import hardware

# Variables globales para sincronización
pago_recibido = threading.Event()
sistema_funcionando = True
ultimo_pago_info = {}
lock = threading.Lock()
inicio_sistema = datetime.now(timezone.utc)

class PaymentMonitor:
    def __init__(self):
        self.pagos_procesados = file_manager.cargar_ids_procesados()
    
    def bucle_monitoreo_fichas(self):
        """Bucle principal de monitoreo de pagos para fichas"""
        global ultimo_pago_info

        logging.info("[INFO] Iniciando monitoreo de pagos para fichas virtuales")
        logging.info("[INFO] Sistema listo para simular fichas físicas")
        logging.info("[INFO] Modo: Solo conexiones de salida (sin puertos abiertos)")

        while sistema_funcionando:
            try:
                logging.info("[INFO] Consultando pagos de fichas...")
                payment_id, monto = mp_handler.consultar_pagos_fichas()

                if payment_id and payment_id not in self.pagos_procesados:
                    detalles = mp_handler.obtener_detalles_pago_completo(payment_id)

                    if detalles:
                        # Validar que el pago no sea anterior al arranque del sistema
                        if self._es_pago_valido(detalles):
                            self._procesar_pago(payment_id, monto, detalles)
                        else:
                            logging.info(f"[INFO] Ignorando pago anterior al arranque del sistema: {payment_id}")
                    else:
                        logging.warning(f"[WARN] No se pudieron obtener detalles de {payment_id}")
                else:
                    logging.info("[INFO] Esperando pagos de fichas...")

            except Exception as e:
                logging.error(f"[ERROR] Error en monitoreo: {e}")

            time.sleep(POLL_INTERVAL)
    
    def _es_pago_valido(self, detalles):
        """Valida si el pago es posterior al arranque del sistema"""
        fecha_pago_str = detalles.get("date_created")
        if fecha_pago_str:
            try:
                # Convertir fecha del pago a UTC
                fecha_pago = datetime.fromisoformat(fecha_pago_str.replace("Z", "+00:00"))
                if fecha_pago.tzinfo is not None:
                    fecha_pago = fecha_pago.astimezone(timezone.utc).replace(tzinfo=None)
                # Convertir inicio_sistema a naive UTC
                inicio_sistema_utc = inicio_sistema.astimezone(timezone.utc).replace(tzinfo=None)
                
                return fecha_pago >= inicio_sistema_utc
            except Exception as e:
                logging.warning(f"[WARN] No se pudo analizar la fecha del pago: {e}")
                return True
        return True
    
    def _procesar_pago(self, payment_id, monto, detalles):
        """Procesa un pago válido"""
        global ultimo_pago_info
        
        with lock:
            logging.info("=" * 70)
            logging.info(f"[PAGO] PAGO DE FICHA DETECTADO! ID: {payment_id}")
            logging.info(f"[PAGO] Monto: ${monto}")
            logging.info("=" * 70)

            ultimo_pago_info = detalles
            pago_recibido.set()

            if file_manager.guardar_ficha_virtual(detalles):
                file_manager.registrar_pago_procesado(payment_id, detalles["date_created"])
                self.pagos_procesados.add(payment_id)

                # Iniciar simulación de ficha en hilo separado
                hilo_ficha = threading.Thread(
                    target=hardware.simular_insercion_ficha,
                    daemon=True
                )
                hilo_ficha.start()

                # Log información del cliente
                self._log_info_cliente(detalles)
                logging.info(f"[OK] Pago {payment_id} procesado - Ficha simulada")

            time.sleep(2)
    
    def _log_info_cliente(self, detalles):
        """Registra información del cliente en los logs"""
        payer = detalles.get("payer", {})
        nombre_completo = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
        if nombre_completo:
            logging.info(f"[CLIENTE] Cliente: {nombre_completo}")
        logging.info(f"[CLIENTE] Email: {payer.get('email', 'No disponible')}")

        payment_method = detalles.get("payment_method", {})
        card = detalles.get("card", {})
        if card:
            logging.info(f"[PAGO] Tarjeta: ****{card.get('last_four_digits', '')}")
            logging.info(f"[PAGO] Titular: {card.get('cardholder_name', 'No disponible')}")
    
    def monitorear_precio_ficha(self):
        """Monitorea cambios en el precio de la ficha"""
        precio_actual = file_manager.leer_precio_ficha()
        
        while sistema_funcionando:
            try:
                nuevo_precio = file_manager.leer_precio_ficha()
                if nuevo_precio != precio_actual:
                    with lock:
                        logging.info(f"[PRECIO] Precio ficha: ${precio_actual:.2f} -> ${nuevo_precio:.2f}")
                        precio_actual = nuevo_precio
                        logging.info("[INFO] QR de ficha se actualizará en la interfaz")
                
                time.sleep(15)  # Revisar precio cada 15 segundos
                
            except Exception as e:
                logging.error(f"[ERROR] Error monitoreando precio: {e}")
                time.sleep(15)

# Instancia global del monitor de pagos
payment_monitor = PaymentMonitor()