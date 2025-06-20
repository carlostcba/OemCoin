# -*- coding: utf-8 -*-
"""
Simulador de Fichas para Lavadero Existente - Version Modularizada
Raspberry Pi + MercadoPago -> Contacto Seco -> Sistema Analógico Original

Autor: Sistema adaptado para reemplazar fichas físicas
Version: 2.1 - Modularizada
Fecha: Junio 2025
"""

import logging
import threading
import time
import sys
import os
from datetime import datetime

# Importar módulos del sistema
from config import LOGS_FILE, LAVADERO_ID, RELAY_PRODUCCION, RELAY_AUXILIAR, PULSO_FICHA_DURACION, PRECIO_DEFAULT, POLL_INTERVAL
from hardware import hardware
from mercadopago_handler import mp_handler
from file_manager import file_manager
from payment_monitor import payment_monitor, sistema_funcionando
from gui_interface import gui_interface

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FILE),
        logging.StreamHandler()
    ]
)

def mostrar_info_sistema():
    """Muestra información del sistema al inicio"""
    logging.info("=" * 80)
    logging.info("SIMULADOR DE FICHAS VIRTUALES PARA LAVADERO - V2.1 MODULARIZADO")
    logging.info("=" * 80)
    logging.info(f"ID Lavadero: {LAVADERO_ID}")
    logging.info(f"GPIO Producción: {RELAY_PRODUCCION}")
    logging.info(f"GPIO Auxiliar: {RELAY_AUXILIAR}")
    logging.info(f"Duración Pulso: {PULSO_FICHA_DURACION} segundos")
    logging.info(f"Precio Default: ${PRECIO_DEFAULT}")
    logging.info(f"Intervalo Polling: {POLL_INTERVAL} segundos")
    logging.info("FUNCIONAMIENTO:")
    logging.info("     Cliente paga con MercadoPago escaneando QR")
    logging.info("     Sistema detecta pago automáticamente")
    logging.info("     Relé de producción simula inserción de ficha")
    logging.info("     Dispositivo analógico controla tiempo y bomba")
    logging.info("     Interfaz muestra información del cliente y pago")
    logging.info("CONECTIVIDAD:")
    logging.info("     Solo conexiones de SALIDA (sin puertos abiertos)")
    logging.info("     Funciona detrás de cualquier router/firewall")
    logging.info("     Requiere únicamente WiFi a Internet")
    logging.info("MEJORAS V2.1 MODULARIZADA:")
    logging.info("     Código dividido en módulos especializados")
    logging.info("     Configuración mediante archivo .env")
    logging.info("     Sin tests automáticos de relés al iniciar")
    logging.info("     Relé auxiliar para uso manual solamente")
    logging.info("     Interfaz visual estilo MercadoPago")
    logging.info("     Información detallada del cliente y pago")
    logging.info("ESTRUCTURA MODULAR:")
    logging.info("     config.py - Configuración y variables de entorno")
    logging.info("     hardware.py - Control de relés y GPIO")
    logging.info("     mercadopago_handler.py - Integración con MercadoPago")
    logging.info("     file_manager.py - Manejo de archivos y persistencia")
    logging.info("     payment_monitor.py - Monitor de pagos en tiempo real")
    logging.info("     gui_interface.py - Interfaz gráfica")
    logging.info("     main.py - Coordinador principal")
    logging.info("TESTS MANUALES:")
    logging.info("     hardware.activar_rele_manual(17, 1.0)  # Producción")
    logging.info("     hardware.activar_rele_manual(27, 1.0)  # Auxiliar")
    logging.info("=" * 80)

def verificar_dependencias():
    """Verifica que todas las dependencias estén disponibles"""
    dependencias_faltantes = []
    
    try:
        import mercadopago
    except ImportError:
        dependencias_faltantes.append("mercadopago")
    
    try:
        import gpiozero
    except ImportError:
        dependencias_faltantes.append("gpiozero")
    
    try:
        import RPi.GPIO
    except ImportError:
        dependencias_faltantes.append("RPi.GPIO")
    
    try:
        import qrcode
    except ImportError:
        dependencias_faltantes.append("qrcode")
    
    try:
        from PIL import Image
    except ImportError:
        dependencias_faltantes.append("Pillow")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        dependencias_faltantes.append("python-dotenv")
    
    if dependencias_faltantes:
        logging.error(f"[ERROR] Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        logging.error("[ERROR] Instale las dependencias con:")
        logging.error(f"[ERROR] pip install {' '.join(dependencias_faltantes)}")
        return False
    
    return True

def inicializar_sistema():
    """Inicializa todos los componentes del sistema"""
    try:
        logging.info("[INIT] Inicializando sistema de fichas virtuales...")
        
        # Verificar dependencias
        if not verificar_dependencias():
            return False
        
        # Inicializar archivos
        file_manager.inicializar_archivos()
        
        # Test de conectividad (sin activar relés)
        if not mp_handler.test_conectividad_fichas():
            logging.error("[ERROR] Sin conectividad - verificar WiFi")
            return False
        
        logging.info("[INFO] Sistema listo - sin tests automáticos de relés")
        logging.info("[INFO] Para test manual usar: hardware.activar_rele_manual(17) o hardware.activar_rele_manual(27)")
        
        return True
        
    except Exception as e:
        logging.error(f"[ERROR] Error inicializando sistema: {e}")
        return False

def iniciar_servicios_background():
    """Inicia los servicios en hilos de background"""
    logging.info("[INFO] Iniciando servicios del simulador...")
    
    # Iniciar monitoreo de pagos (hilo en background)
    hilo_monitoreo = threading.Thread(
        target=payment_monitor.bucle_monitoreo_fichas, 
        daemon=True,
        name="MonitoreoPagos"
    )
    hilo_monitoreo.start()
    
    # Iniciar monitoreo de precio (hilo en background)
    hilo_precio = threading.Thread(
        target=payment_monitor.monitorear_precio_ficha, 
        daemon=True,
        name="MonitoreoPrecios"
    )
    hilo_precio.start()
    
    logging.info("[OK] Todos los servicios iniciados correctamente")
    
    return hilo_monitoreo, hilo_precio

def main():
    """Función principal del simulador"""
    global sistema_funcionando
    
    try:
        # Mostrar información del sistema
        mostrar_info_sistema()
        
        # Inicializar sistema
        if not inicializar_sistema():
            logging.error("[ERROR] Fallo en la inicialización del sistema")
            return 1
        
        # Iniciar servicios en background
        hilos_servicios = iniciar_servicios_background()
        
        logging.info("[INFO] Iniciando interfaz de simulador estilo MercadoPago...")
        
        # Interfaz principal (hilo principal)
        gui_interface.mostrar_interfaz_simulador()
        
        return 0
        
    except KeyboardInterrupt:
        logging.info("[INFO] Apagando simulador de fichas...")
        sistema_funcionando = False
        hardware.apagar_relais()
        return 0
        
    except Exception as e:
        logging.error(f"[ERROR] Error crítico en simulador: {e}")
        sistema_funcionando = False
        hardware.apagar_relais()
        return 1
        
    finally:
        # Cleanup final
        sistema_funcionando = False
        hardware.apagar_relais()
        logging.info("[INFO] Simulador de fichas apagado correctamente")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)