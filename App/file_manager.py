# -*- coding: utf-8 -*-
"""
Manejo de archivos y persistencia de datos del simulador de fichas
"""
import json
import os
import logging
from datetime import datetime
from config import (
    PRECIO_PATH, LOG_PATH, PAGOS_PROCESADOS_PATH, 
    LAVADERO_ID, PRECIO_DEFAULT, PULSO_FICHA_DURACION, RELAY_PRODUCCION
)

class FileManager:
    def __init__(self):
        self.pagos_procesados = self.cargar_ids_procesados()
    
    def cargar_ids_procesados(self):
        """Carga IDs de pagos ya procesados"""
        pagos = set()
        try:
            with open(PAGOS_PROCESADOS_PATH, "r") as f:
                for linea in f:
                    partes = linea.strip().split()
                    if partes:
                        pagos.add(partes[0])
        except FileNotFoundError:
            logging.info("[INFO] Archivo pagos_procesados.txt no existe. Se creará nuevo.")
        return pagos
    
    def registrar_pago_procesado(self, payment_id, fecha):
        """Registra un pago como procesado"""
        try:
            with open(PAGOS_PROCESADOS_PATH, "a") as f:
                f.write(f"{payment_id} {fecha}\n")
            self.pagos_procesados.add(payment_id)
        except Exception as e:
            logging.error(f"[ERROR] No se pudo registrar pago procesado: {e}")
    
    def leer_precio_ficha(self):
        """Lee el precio de la ficha desde archivo"""
        try:
            with open(PRECIO_PATH, 'r') as f:
                valor = f.read().strip()
                precio = float(valor)
                if precio <= 0:
                    logging.warning(f"[WARN] Precio inválido: {precio}. Usando ${PRECIO_DEFAULT}")
                    return PRECIO_DEFAULT
                return precio
        except FileNotFoundError:
            logging.info("[INFO] Creando archivo de precio de ficha por defecto")
            with open(PRECIO_PATH, 'w') as f:
                f.write(str(PRECIO_DEFAULT))
            return PRECIO_DEFAULT
        except ValueError:
            logging.error("[ERROR] Error: precio debe ser un número")
            return PRECIO_DEFAULT
        except Exception as e:
            logging.error(f"[ERROR] Error leyendo precio: {e}")
            return PRECIO_DEFAULT
    
    def guardar_ficha_virtual(self, payment_details):
        """Guarda registro de la ficha virtual procesada"""
        try:
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
                "gpio_utilizado": RELAY_PRODUCCION,
                "payment_details": payment_details
            }
            
            with open(archivo, "w", encoding='utf-8') as f:
                json.dump(data_ficha, f, indent=2, ensure_ascii=False)
                
            logging.info(f"[OK] Ficha virtual registrada: {archivo}")
            return True
            
        except Exception as e:
            logging.error(f"[ERROR] Error guardando ficha: {e}")
            return False
    
    def cargar_fichas_procesadas(self):
        """Carga IDs de fichas ya procesadas desde archivos JSON"""
        procesadas = set()
        try:
            if os.path.exists(LOG_PATH):
                for archivo in os.listdir(LOG_PATH):
                    if archivo.endswith('.json'):
                        partes = archivo.replace('.json', '').split('_')
                        if len(partes) >= 2:
                            payment_id = '_'.join(partes[1:])
                            procesadas.add(payment_id)
                            
            logging.info(f"[INFO] {len(procesadas)} fichas ya procesadas")
            return procesadas
            
        except Exception as e:
            logging.error(f"[ERROR] Error cargando fichas procesadas: {e}")
            return set()
    
    def inicializar_archivos(self):
        """Inicializa archivos necesarios del sistema"""
        # Crear archivo de precio si no existe
        if not os.path.exists(PRECIO_PATH):
            with open(PRECIO_PATH, 'w') as f:
                f.write(str(PRECIO_DEFAULT))
            logging.info("[INFO] Archivo de precio de ficha creado")

# Instancia global del manejador de archivos
file_manager = FileManager()