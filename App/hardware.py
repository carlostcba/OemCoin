# -*- coding: utf-8 -*-
"""
Manejo del hardware (relés y GPIO) del simulador de fichas
"""
import time
import logging
import threading
from gpiozero import OutputDevice
import RPi.GPIO as GPIO
from config import RELAY_PRODUCCION, RELAY_AUXILIAR, PULSO_FICHA_DURACION

# Variables globales para control de estado
ficha_activada = threading.Event()
ultimo_pago_info = {}
lock = threading.Lock()

class HardwareController:
    def __init__(self):
        self.contacto_ficha = None
        self.contacto_aux = None
        self.inicializar_hardware()
    
    def inicializar_hardware(self):
        """Inicializa los contactos secos de manera segura"""
        try:
            logging.info("[INIT] Configurando contactos seguros...")
            
            # Cleanup completo previo
            try:
                GPIO.setmode(GPIO.BCM)
                logging.info("[INIT] Cleanup GPIO completado")
            except Exception:
                pass
            
            # Configurar relés con máxima seguridad
            self.contacto_ficha = OutputDevice(RELAY_PRODUCCION, active_high=True, initial_value=False)
            self.contacto_aux = OutputDevice(RELAY_AUXILIAR, active_high=True, initial_value=False)
            
            # Forzar OFF inmediatamente
            self.contacto_ficha.off()
            self.contacto_aux.off()
            time.sleep(0.1)
            
            # Verificación final
            if self.contacto_ficha.value == 0 and self.contacto_aux.value == 0:
                logging.info("[SEGURIDAD] ✓ Todos los relés en estado OFF")
            else:
                logging.error("[ALERTA] ⚠ Relés no están en OFF correctamente")
                self.contacto_ficha.off()
                self.contacto_aux.off()
            
            logging.info(f"[OK] Contacto PRODUCCIÓN configurado en GPIO {RELAY_PRODUCCION}")
            logging.info(f"[OK] Contacto AUXILIAR configurado en GPIO {RELAY_AUXILIAR}")
            logging.info("[INFO] GPIO 17: Producción (solo pagos)")
            logging.info("[INFO] GPIO 27: Auxiliar (uso manual)")
            
        except Exception as e:
            logging.error(f"[ERROR] Error configurando contactos: {e}")
            raise
    
    def activar_rele_manual(self, gpio_pin, duracion=1.0):
        """Activa un relé manualmente desde línea de comando"""
        try:
            if gpio_pin == RELAY_PRODUCCION:
                contacto = self.contacto_ficha
                tipo = "PRODUCCIÓN"
            elif gpio_pin == RELAY_AUXILIAR:
                contacto = self.contacto_aux
                tipo = "AUXILIAR"
            else:
                logging.error(f"[ERROR] GPIO {gpio_pin} no válido")
                return False
                
            logging.info(f"[MANUAL] Activando {tipo} (GPIO {gpio_pin}) por {duracion} segundos")
            contacto.on()
            time.sleep(duracion)
            contacto.off()
            logging.info(f"[OK] {tipo} desactivado")
            return True
            
        except Exception as e:
            logging.error(f"[ERROR] Error activando relé: {e}")
            return False
    
    def simular_insercion_ficha(self):
        """Simula la inserción de una ficha física activando el contacto seco"""
        global ultimo_pago_info
        
        # Validación: solo producción con pago confirmado
        if not ultimo_pago_info:
            logging.warning("[SEGURIDAD] Bloqueando activación sin pago confirmado")
            return False
        
        try:
            contacto = self.contacto_ficha
            gpio = RELAY_PRODUCCION
            
            logging.info("=" * 60)
            logging.info(f"[FICHA] SIMULANDO INSERCIÓN DE FICHA - PRODUCCIÓN")
            logging.info(f"[FICHA] Activando GPIO {gpio} por {PULSO_FICHA_DURACION} segundos")
            logging.info("=" * 60)
            
            # Activar contacto seco (simula ficha insertada)
            contacto.on()
            ficha_activada.set()
            
            # Countdown visual en logs
            for i in range(int(PULSO_FICHA_DURACION), 0, -1):
                logging.info(f"[FICHA] Contacto ACTIVO - {i} segundos restantes")
                time.sleep(1)
            
            # Desactivar contacto
            contacto.off()
            
            logging.info("=" * 60)
            logging.info(f"[OK] FICHA SIMULADA COMPLETADA")
            logging.info("[INFO] El dispositivo analógico toma el control")
            logging.info("[INFO] Tiempo y bomba manejados por sistema existente")
            logging.info("=" * 60)
            
            # Mantener señal de ficha activada por unos segundos para la interfaz
            time.sleep(3)
            ficha_activada.clear()
            
            return True
            
        except Exception as e:
            logging.error(f"[ERROR] Error simulando ficha: {e}")
            contacto.off()
            ficha_activada.clear()
            return False
    
    def apagar_relais(self):
        """Apaga todos los relés de manera segura"""
        try:
            if self.contacto_ficha:
                self.contacto_ficha.off()
            if self.contacto_aux:
                self.contacto_aux.off()
            logging.info("[SEGURIDAD] Todos los relés apagados")
        except Exception as e:
            logging.error(f"[ERROR] Error apagando relés: {e}")

# Instancia global del controlador de hardware
hardware = HardwareController()