# -*- coding: utf-8 -*-
"""
Simulador de Fichas para Lavadero Existente - Version Mejorada
Raspberry Pi + MercadoPago -> Contacto Seco -> Sistema Analogico Original

MEJORAS:
- Rele auxiliar (GPIO 27) para uso manual
- Rele de produccion (GPIO 17) para funcionamiento real
- Interfaz visual mejorada estilo MercadoPago
- Informacion detallada del pago y cliente
- Notificaciones visuales de pago recibido
- Sin tests automaticos al iniciar

Autor: Sistema adaptado para reemplazar fichas fisicas
Version: 2.1 - Sin Tests Automaticos
Fecha: Junio 2025
"""

import json
import time
import threading
import os
import logging
from datetime import datetime, timezone
from gpiozero import OutputDevice
from PIL import Image, ImageTk, ImageDraw, ImageFont
import qrcode
import RPi.GPIO as GPIO

# SDK oficial de MercadoPago
import mercadopago

# Verificar entorno grafico
if os.environ.get("DISPLAY"):
    import tkinter as tk
    from tkinter import ttk
else:
    print("[!] No se detecto entorno grafico. No se mostrara QR en pantalla HDMI.")

# === CONFIGURACION SISTEMA DE FICHAS MEJORADO ===
RELAY_PIN = 17  # Pin GPIO para produccion (ficha real)
RELAY_PIN_AUX = 27  # Pin GPIO auxiliar para uso manual

# Claves de produccion MercadoPago
PUBLIC_KEY = "APP_USR-d33672d1-2db8-48fc-b18a-37b3018bbcf5"
ACCESS_TOKEN = "APP_USR-3033042189313629-082719-d74d77377d6eefe870db67befeca41c7-147894512"

LAVADERO_ID = "LAV-001"
APP_PATH = "/home/oemspot/App"
LOG_PATH = "/home/oemspot/App/pagos_fichas"
PRECIO_PATH = "/home/oemspot/App/precio_ficha.txt"
LOGS_FILE = "/home/oemspot/App/simulador_fichas.log"
QR_TEMP_PATH = "/home/oemspot/App/qr_ficha.png"
PAGOS_PROCESADOS_PATH = "/home/oemspot/App/pagos_procesados.txt"

# Configuracion especifica para contacto seco
POLL_INTERVAL = 3  # Consultar cada 3 segundos
PULSO_FICHA_DURACION = 1.0  # Duracion del pulso para simular ficha (1 segundo)
PRECIO_DEFAULT = 1.0  # Precio por ficha por defecto

# Crear directorio si no existe
os.makedirs(APP_PATH, exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FILE),
        logging.StreamHandler()
    ]
)

# === INICIALIZAR SDK ===
try:
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    logging.info("[OK] SDK MercadoPago inicializado para simulador de fichas")
except Exception as e:
    logging.error(f"[ERROR] Error inicializando SDK: {e}")
    exit(1)

# === HARDWARE - CONTACTOS SECOS - VERSION DEFINITIVA ===
try:
    logging.info("[INIT] Configurando contactos seguros...")
    
    # Cleanup completo previo
    try:
        import RPi.GPIO as GPIO_CHECK
        GPIO_CHECK.setmode(GPIO_CHECK.BCM)
        # GPIO_CHECK.cleanup()
        logging.info("[INIT] Cleanup GPIO completado")
    except Exception:
        pass  # Ignorar errores de cleanup
    
    # Configurar reles con maxima seguridad
    contacto_ficha = OutputDevice(RELAY_PIN, active_high=True, initial_value=False)
    contacto_aux = OutputDevice(RELAY_PIN_AUX, active_high=True, initial_value=False)
    
    # Forzar OFF inmediatamente
    contacto_ficha.off()
    contacto_aux.off()
    time.sleep(0.1)  # Peque�a pausa para asegurar
    
    # Verificacion final
    if contacto_ficha.value == 0 and contacto_aux.value == 0:
        logging.info("[SEGURIDAD] ? Todos los reles en estado OFF")
    else:
        logging.error("[ALERTA] ? Reles no estan en OFF correctamente")
        # Forzar OFF nuevamente
        contacto_ficha.off()
        contacto_aux.off()
    
    logging.info(f"[OK] Contacto PRODUCCION configurado en GPIO {RELAY_PIN}")
    logging.info(f"[OK] Contacto AUXILIAR configurado en GPIO {RELAY_PIN_AUX}")
    logging.info("[INFO] GPIO 17: Produccion (solo pagos)")
    logging.info("[INFO] GPIO 27: Auxiliar (uso manual)")
    
except Exception as e:
    logging.error(f"[ERROR] Error configurando contactos: {e}")
    exit(1)

# Variables globales para sincronizacion
lock = threading.Lock()
precio_ficha = PRECIO_DEFAULT
qr_link_actual = None
ficha_activada = threading.Event()
pago_recibido = threading.Event()
sistema_funcionando = True
preference_id_actual = None
ultimo_pago_info = {}

# === FUNCIONES ESPECIFICAS PARA SISTEMA DE FICHAS ===

def cargar_ids_procesados():
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

def registrar_pago_procesado(payment_id, fecha):
    try:
        with open(PAGOS_PROCESADOS_PATH, "a") as f:
            f.write(f"{payment_id} {fecha}\n")
    except Exception as e:
        logging.error(f"[ERROR] No se pudo registrar pago procesado: {e}")

def leer_precio_ficha():
    """Lee el precio de la ficha desde archivo"""
    try:
        with open(PRECIO_PATH, 'r') as f:
            valor = f.read().strip()
            precio = float(valor)
            if precio <= 0:
                logging.warning(f"[WARN] Precio invalido: {precio}. Usando ${PRECIO_DEFAULT}")
                return PRECIO_DEFAULT
            return precio
    except FileNotFoundError:
        logging.info("[INFO] Creando archivo de precio de ficha por defecto")
        with open(PRECIO_PATH, 'w') as f:
            f.write(str(PRECIO_DEFAULT))
        return PRECIO_DEFAULT
    except ValueError:
        logging.error("[ERROR] Error: precio debe ser un numero")
        return PRECIO_DEFAULT
    except Exception as e:
        logging.error(f"[ERROR] Error leyendo precio: {e}")
        return PRECIO_DEFAULT

def generar_qr_ficha(precio):
    """Genera QR para compra de ficha virtual"""
    global preference_id_actual
    
    try:
        timestamp = int(time.time())
        external_reference = f"{LAVADERO_ID}-FICHA-{timestamp}"
        
        preference_data = {
            "items": [
                {
                    "title": f"Ficha Virtual Lavadero {LAVADERO_ID}",
                    "description": "Ficha digital para lavado automatico",
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
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            preference_id_actual = preference["id"]
            init_point = preference["init_point"]
            
            logging.info(f"[OK] QR de ficha generado - ID: {preference_id_actual}")
            return init_point
        else:
            logging.error(f"[ERROR] Error creando preferencia de ficha: {preference_response}")
            return "https://www.mercadopago.com.ar"
            
    except Exception as e:
        logging.error(f"[ERROR] Error generando QR de ficha: {e}")
        return "https://www.mercadopago.com.ar"

def consultar_pagos_fichas():
    """Consulta pagos de fichas virtuales usando solo conexiones de salida"""
    try:
        search_params = {
            "sort": "date_created",
            "criteria": "desc",
            "range": "date_created", 
            "begin_date": "NOW-1DAYS",
            "end_date": "NOW"
        }
        
        payments_response = sdk.payment().search(search_params)
        
        if payments_response["status"] == 200:
            results = payments_response["response"].get("results", [])
            
            # Buscar pagos aprobados de fichas de este lavadero
            for pago in results:
                if (pago.get("status") == "approved" and 
                    (pago.get("external_reference") or "").startswith(f"{LAVADERO_ID}-FICHA")):
                    
                    return pago["id"], pago.get("transaction_amount", 0)
            
            return None, 0
        else:
            logging.warning(f"[WARN] Error en busqueda de pagos: {payments_response}")
            return None, 0
            
    except Exception as e:
        logging.error(f"[ERROR] Error consultando pagos de fichas: {e}")
        return None, 0

def obtener_detalles_pago_completo(payment_id):
    """Obtiene detalles completos del pago incluyendo informacion del pagador"""
    try:
        payment_response = sdk.payment().get(payment_id)
        
        if payment_response["status"] == 200:
            payment_data = payment_response["response"]
            
            # Extraer informacion util del pago
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
            
            # Informacion del pagador
            payer = payment_data.get("payer", {})
            pago_info["payer"] = {
                "email": payer.get("email", "No disponible"),
                "first_name": payer.get("first_name", ""),
                "last_name": payer.get("last_name", ""),
                "identification": payer.get("identification", {}),
                "phone": payer.get("phone", {})
            }
            
            # Metodo de pago
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

def guardar_ficha_virtual(payment_details):
    """Guarda registro de la ficha virtual procesada"""
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
            
        logging.info(f"[OK] Ficha virtual registrada: {archivo}")
        return True
        
    except Exception as e:
        logging.error(f"[ERROR] Error guardando ficha: {e}")
        return False

def cargar_fichas_procesadas():
    """Carga IDs de fichas ya procesadas"""
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

def activar_rele_manual(gpio_pin, duracion=1.0):
    """Activa un rele manualmente desde linea de comando"""
    try:
        if gpio_pin == RELAY_PIN:
            contacto = contacto_ficha
            tipo = "PRODUCCION"
        elif gpio_pin == RELAY_PIN_AUX:
            contacto = contacto_aux
            tipo = "AUXILIAR"
        else:
            logging.error(f"[ERROR] GPIO {gpio_pin} no valido")
            return False
            
        logging.info(f"[MANUAL] Activando {tipo} (GPIO {gpio_pin}) por {duracion} segundos")
        contacto.on()
        time.sleep(duracion)
        contacto.off()
        logging.info(f"[OK] {tipo} desactivado")
        return True
        
    except Exception as e:
        logging.error(f"[ERROR] Error activando rele: {e}")
        return False

def simular_insercion_ficha():
    """Simula la insercion de una ficha fisica activando el contacto seco"""
    global ultimo_pago_info
    
    # Validacion: solo produccion con pago confirmado
    if not ultimo_pago_info:
        logging.warning("[SEGURIDAD] Bloqueando activacion sin pago confirmado")
        return False
    
    try:
        # Solo usar rele de produccion
        contacto = contacto_ficha
        gpio = RELAY_PIN
        
        logging.info("=" * 60)
        logging.info(f"[FICHA] SIMULANDO INSERCION DE FICHA - PRODUCCION")
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
        logging.info("[INFO] El dispositivo analogico toma el control")
        logging.info("[INFO] Tiempo y bomba manejados por sistema existente")
        logging.info("=" * 60)
        
        # Mantener se al de ficha activada por unos segundos para la interfaz
        time.sleep(3)
        ficha_activada.clear()
        
        return True
        
    except Exception as e:
        logging.error(f"[ERROR] Error simulando ficha: {e}")
        contacto.off()
        ficha_activada.clear()
        return False

inicio_sistema = datetime.now(timezone.utc)

def bucle_monitoreo_fichas():
    """Bucle principal de monitoreo de pagos para fichas"""
    global ultimo_pago_info

    pagos_procesados = cargar_ids_procesados()

    logging.info("[INFO] Iniciando monitoreo de pagos para fichas virtuales")
    logging.info("[INFO] Sistema listo para simular fichas fisicas")
    logging.info("[INFO] Modo: Solo conexiones de salida (sin puertos abiertos)")

    while sistema_funcionando:
        try:
            logging.info("[INFO] Consultando pagos de fichas...")
            payment_id, monto = consultar_pagos_fichas()

            if payment_id and payment_id not in pagos_procesados:
                detalles = obtener_detalles_pago_completo(payment_id)

                if detalles:
                    # Validar que el pago no sea anterior al arranque del sistema
                    fecha_pago_str = detalles.get("date_created")
                    if fecha_pago_str:
                        try:
                            # Convertir fecha del pago a UTC
                            fecha_pago = datetime.fromisoformat(fecha_pago_str.replace("Z", "+00:00"))
                            if fecha_pago.tzinfo is not None:
                                fecha_pago = fecha_pago.astimezone(timezone.utc).replace(tzinfo=None)
                            # Convertir inicio_sistema a naive UTC
                            inicio_sistema_utc = inicio_sistema.astimezone(timezone.utc).replace(tzinfo=None)
                            
                            if fecha_pago < inicio_sistema_utc:
                                logging.info(f"[INFO] Ignorando pago anterior al arranque del sistema: {payment_id}")
                                continue

                        except Exception as e:
                            logging.warning(f"[WARN] No se pudo analizar la fecha del pago: {e}")

                    with lock:
                        logging.info("=" * 70)
                        logging.info(f"[PAGO] PAGO DE FICHA DETECTADO! ID: {payment_id}")
                        logging.info(f"[PAGO] Monto: ${monto}")
                        logging.info("=" * 70)

                        ultimo_pago_info = detalles
                        pago_recibido.set()

                        if guardar_ficha_virtual(detalles):
                            registrar_pago_procesado(payment_id, detalles["date_created"])
                            pagos_procesados.add(payment_id)

                            hilo_ficha = threading.Thread(
                                target=simular_insercion_ficha,
                                daemon=True
                            )
                            hilo_ficha.start()

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

                            logging.info(f"[OK] Pago {payment_id} procesado - Ficha simulada")

                        time.sleep(2)
                else:
                    logging.warning(f"[WARN] No se pudieron obtener detalles de {payment_id}")
            else:
                logging.info("[INFO] Esperando pagos de fichas...")

        except Exception as e:
            logging.error(f"[ERROR] Error en monitoreo: {e}")

        time.sleep(POLL_INTERVAL)

def monitorear_precio_ficha():
    """Monitorea cambios en el precio de la ficha"""
    global precio_ficha, qr_link_actual
    
    while sistema_funcionando:
        try:
            nuevo_precio = leer_precio_ficha()
            if nuevo_precio != precio_ficha:
                with lock:
                    logging.info(f"[PRECIO] Precio ficha: ${precio_ficha:.2f} -> ${nuevo_precio:.2f}")
                    precio_ficha = nuevo_precio
                    qr_link_actual = generar_qr_ficha(precio_ficha)
                    logging.info("[INFO] QR de ficha actualizado")
            
            time.sleep(15)  # Revisar precio cada 15 segundos
            
        except Exception as e:
            logging.error(f"[ERROR] Error monitoreando precio: {e}")
            time.sleep(15)

def mostrar_interfaz_simulador():
    """Interfaz grafica del simulador de fichas estilo MercadoPago"""
    global precio_ficha, qr_link_actual, ultimo_pago_info
    
    # Inicializar
    precio_ficha = leer_precio_ficha()
    qr_link_actual = generar_qr_ficha(precio_ficha)
    
    # Generar QR
    qr = qrcode.make(qr_link_actual)
    qr.save(QR_TEMP_PATH)
    
    if not os.environ.get("DISPLAY"):
        logging.info("[INFO] Sin entorno grafico - funcionando en modo consola")
        while sistema_funcionando:
            time.sleep(1)
        return

    root = tk.Tk()
    root.title("Lavadero - Pago con MercadoPago")
    root.configure(bg='#00A0E6')  # Azul MercadoPago
    
    # Frame principal
    main_frame = tk.Frame(root, bg='#00A0E6')
    main_frame.pack(expand=True, fill='both', padx=40, pady=30)
    
    # Header con logo MercadoPago simulado
    header_frame = tk.Frame(main_frame, bg='#00A0E6')
    header_frame.pack(fill='x', pady=(0, 20))
    
    # Logo y titulo
    title_label = tk.Label(
        header_frame,
        text="Pagar con MercadoPago",
        font=("Roboto", 32, "bold"),
        fg='white',
        bg='#00A0E6'
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        header_frame,
        text="Ficha Virtual - Lavadero Automatico",
        font=("Roboto", 18),
        fg='#E3F2FD',
        bg='#00A0E6'
    )
    subtitle_label.pack(pady=(5, 0))
    
    # Container principal blanco
    container = tk.Frame(main_frame, bg='#ededed', relief='flat', bd=0)
    container.pack(expand=True, fill='both', padx=20, pady=20)
    
    # Padding interno
    content_frame = tk.Frame(container, bg='#ededed')
    content_frame.pack(expand=True, fill='both', padx=40, pady=40)
    
    # Precio destacado
    precio_frame = tk.Frame(content_frame, bg='#ededed')
    precio_frame.pack(fill='x', pady=(0, 30))
    
    precio_label = tk.Label(
        precio_frame,
        text=f"${precio_ficha:.0f}",
        font=("Roboto", 48, "bold"),
        fg='#00A0E6',
        bg='#ededed'
    )
    precio_label.pack()
    
    desc_precio = tk.Label(
        precio_frame,
        text="Precio por ficha virtual",
        font=("Roboto", 16),
        fg='#666666',
        bg='#ededed'
    )
    desc_precio.pack()
    
    # QR Code con frame
    qr_frame = tk.Frame(content_frame, bg='#ededed')
    qr_frame.pack(pady=20)
    
    qr_container = tk.Frame(qr_frame, bg='#F5F5F5', relief='solid', bd=1)
    qr_container.pack(padx=20, pady=20)
    
    img = Image.open(QR_TEMP_PATH)
    img = img.resize((300, 300), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)
    qr_label = tk.Label(qr_container, image=tk_img, bg='#F5F5F5')
    qr_label.pack(padx=15, pady=15)
    
    # Instrucciones
    instruc_label = tk.Label(
        content_frame,
        text="1. Escanee el codigo QR con su celular\n2. Complete el pago en la app de MercadoPago\n3. El lavado se activara automaticamente",
        font=("Roboto", 16),
        fg='#333333',
        bg='#ededed',
        justify='center'
    )
    instruc_label.pack(pady=(20, 30))
    
    # Estado con estilo MercadoPago
    estado_frame = tk.Frame(content_frame, bg='#ededed')
    estado_frame.pack(fill='x', pady=20)
    
    estado_label = tk.Label(
        estado_frame,
        text="Esperando el pago...",
        font=("Roboto", 20, "bold"),
        fg='#00a0e6',
        bg='#ededed'
    )
    estado_label.pack()
    
    # Frame para informacion del pago (inicialmente oculto)
    pago_info_frame = tk.Frame(content_frame, bg='#E8F5E8', relief='solid', bd=1)
    
    def mostrar_info_pago():
        """Muestra la informacion del pago recibido"""
        if ultimo_pago_info:
            # Limpiar frame anterior
            for widget in pago_info_frame.winfo_children():
                widget.destroy()
            
            # Titulo del pago
            titulo_pago = tk.Label(
                pago_info_frame,
                text="PAGO RECIBIDO!",
                font=("Roboto", 24, "bold"),
                fg='#2E7D32',
                bg='#E8F5E8'
            )
            titulo_pago.pack(pady=(15, 10))
            
            # Monto
            monto = ultimo_pago_info.get("transaction_amount", 0)
            monto_label = tk.Label(
                pago_info_frame,
                text=f"${monto:.2f} ARS",
                font=("Roboto", 32, "bold"),
                fg='#1B5E20',
                bg='#E8F5E8'
            )
            monto_label.pack(pady=5)
            
            # Informacion del cliente
            payer = ultimo_pago_info.get("payer", {})
            nombre_completo = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
            
            if nombre_completo:
                cliente_label = tk.Label(
                    pago_info_frame,
                    text=f"Cliente: {nombre_completo}",
                    font=("Roboto", 18, "bold"),
                    fg='#2E7D32',
                    bg='#E8F5E8'
                )
                cliente_label.pack(pady=2)
            
            # Email del cliente
            email = payer.get("email", "")
            if email and email != "No disponible":
                email_label = tk.Label(
                    pago_info_frame,
                    text=f"Email: {email}",
                    font=("Roboto", 14),
                    fg='#388E3C',
                    bg='#E8F5E8'
                )
                email_label.pack(pady=2)
            
            # Metodo de pago
            payment_method = ultimo_pago_info.get("payment_method", {})
            card = ultimo_pago_info.get("card", {})
            
            if card:
                tarjeta_info = f"Tarjeta: ****{card.get('last_four_digits', '')}"
                tarjeta_label = tk.Label(
                    pago_info_frame,
                    text=tarjeta_info,
                    font=("Roboto", 14),
                    fg='#388E3C',
                    bg='#E8F5E8'
                )
                tarjeta_label.pack(pady=2)
            
            # ID de transaccion
            payment_id = str(ultimo_pago_info.get("id", ""))[:20]
            id_label = tk.Label(
                pago_info_frame,
                text=f"ID: {payment_id}...",
                font=("Roboto", 12),
                fg='#666666',
                bg='#E8F5E8'
            )
            id_label.pack(pady=(10, 15))
            
            # Mostrar el frame
            pago_info_frame.pack(fill='x', pady=20)
    
    # Info tecnica en la parte inferior
    tech_frame = tk.Frame(main_frame, bg='#00A0E6')
    tech_frame.pack(fill='x', pady=(10, 0))
    
    if preference_id_actual:
        tech_label = tk.Label(
            tech_frame,
            text=f"Copyright 2025 OemCoin",
            font=("Roboto", 12),
            fg='#B3E5FC',
            bg='#00A0E6'
        )
        tech_label.pack()
    
    def actualizar_interfaz_simulador():
        """Actualiza la interfaz segun el estado"""
        while sistema_funcionando:
            try:
                if pago_recibido.is_set():
                    # Pago recibido - mostrar informacion
                    estado_label.config(
                        text="Activando lavadero...",
                        fg='#2E7D32'
                    )
                    precio_label.config(fg='#2E7D32')
                    
                    # Mostrar informacion del pago
                    mostrar_info_pago()
                    
                    # Esperar un poco y luego resetear
                    time.sleep(8)
                    pago_recibido.clear()
                    
                    # Ocultar info del pago y volver al estado normal
                    pago_info_frame.pack_forget()
                    estado_label.config(
                        text="Esperando el pago...",
                        fg='#00a0e6'
                    )
                    precio_label.config(fg='#fbc02d')
                    
                elif ficha_activada.is_set():
                    # Ficha siendo activada
                    estado_label.config(
                        text="Activando ficha virtual...",
                        fg='#00a0e6'
                    )
                    
                else:
                    # Estado normal
                    # Actualizar precio si cambio
                    with lock:
                        precio_label.config(text=f"${precio_ficha:.0f}")
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"[ERROR] Error actualizando interfaz: {e}")
                time.sleep(1)
    
    # Iniciar actualizacion de interfaz
    threading.Thread(target=actualizar_interfaz_simulador, daemon=True).start()
    
    # Configurar pantalla completa
    root.attributes('-fullscreen', True)
    root.bind('<Escape>', lambda e: cerrar_simulador())
    root.bind('<F11>', lambda e: root.attributes('-fullscreen', False))
    
    def cerrar_simulador():
        global sistema_funcionando
        sistema_funcionando = False
        contacto_ficha.off()
        contacto_aux.off()
        root.quit()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        cerrar_simulador()

def test_conectividad_fichas():
    """Prueba la conectividad para sistema de fichas"""
    try:
        logging.info("[TEST] Probando conectividad para fichas...")
        
        test_data = {
            "items": [{"title": "Test Ficha", "quantity": 1, "unit_price": 1}]
        }
        
        response = sdk.preference().create(test_data)
        if response["status"] == 201:
            logging.info("[OK] Conectividad OK para fichas")
            return True
        else:
            logging.error(f"[ERROR] Error de conectividad: {response}")
            return False
            
    except Exception as e:
        logging.error(f"[ERROR] Error probando conectividad: {e}")
        return False

def mostrar_info_sistema():
    """Muestra informacion del sistema al inicio"""
    logging.info("=" * 80)
    logging.info("SIMULADOR DE FICHAS VIRTUALES PARA LAVADERO - V2.1")
    logging.info("=" * 80)
    logging.info(f"ID Lavadero: {LAVADERO_ID}")
    logging.info(f"GPIO Produccion: {RELAY_PIN}")
    logging.info(f"GPIO Auxiliar: {RELAY_PIN_AUX}")
    logging.info(f"Duracion Pulso: {PULSO_FICHA_DURACION} segundos")
    logging.info(f"Precio Default: ${PRECIO_DEFAULT}")
    logging.info(f"Intervalo Polling: {POLL_INTERVAL} segundos")
    logging.info("FUNCIONAMIENTO:")
    logging.info("     Cliente paga con MercadoPago escaneando QR")
    logging.info("     Sistema detecta pago automaticamente")
    logging.info("     Rele de produccion simula insercion de ficha")
    logging.info("     Dispositivo analogico controla tiempo y bomba")
    logging.info("     Interfaz muestra informacion del cliente y pago")
    logging.info("CONECTIVIDAD:")
    logging.info("     Solo conexiones de SALIDA (sin puertos abiertos)")
    logging.info("     Funciona detras de cualquier router/firewall")
    logging.info("     Requiere unicamente WiFi a Internet")
    logging.info("MEJORAS V2.1:")
    logging.info("     Sin tests automaticos de reles al iniciar")
    logging.info("     Rele auxiliar para uso manual solamente")
    logging.info("     Interfaz visual estilo MercadoPago")
    logging.info("     Informacion detallada del cliente y pago")
    logging.info("     Notificaciones visuales mejoradas")
    logging.info("TESTS MANUALES:")
    logging.info("     activar_rele_manual(17, 1.0)  # Produccion")
    logging.info("     activar_rele_manual(27, 1.0)  # Auxiliar")
    logging.info("=" * 80)

# === EJECUCION PRINCIPAL ===
if __name__ == "__main__":
    try:
        # Mostrar informacion del sistema
        mostrar_info_sistema()
        
        # Crear directorios necesarios
        os.makedirs(APP_PATH, exist_ok=True)
        os.makedirs(LOG_PATH, exist_ok=True)
        
        # Crear archivo de precio si no existe
        if not os.path.exists(PRECIO_PATH):
            with open(PRECIO_PATH, 'w') as f:
                f.write(str(PRECIO_DEFAULT))
            logging.info("[INFO] Archivo de precio de ficha creado")
        
        # Test de conectividad (sin activar reles)
        if not test_conectividad_fichas():
            logging.error("[ERROR] Sin conectividad - verificar WiFi")
            exit(1)
        
        logging.info("[INFO] Sistema listo - sin tests automaticos de reles")
        logging.info("[INFO] Para test manual usar: activar_rele_manual(17) o activar_rele_manual(27)")
        
        # Iniciar servicios del simulador
        logging.info("[INFO] Iniciando servicios del simulador...")
        
        # Iniciar monitoreo de pagos (hilo en background)
        hilo_monitoreo = threading.Thread(target=bucle_monitoreo_fichas, daemon=True)
        hilo_monitoreo.start()
        
        # Iniciar monitoreo de precio (hilo en background)
        hilo_precio = threading.Thread(target=monitorear_precio_ficha, daemon=True)
        hilo_precio.start()
        
        logging.info("[OK] Todos los servicios iniciados correctamente")
        logging.info("[INFO] Iniciando interfaz de simulador estilo MercadoPago...")
        
        # Interfaz principal (hilo principal)
        mostrar_interfaz_simulador()
        
    except KeyboardInterrupt:
        logging.info("[INFO] Apagando simulador de fichas...")
        sistema_funcionando = False
        contacto_ficha.off()
        contacto_aux.off()
    except Exception as e:
        logging.error(f"[ERROR] Error critico en simulador: {e}")
        sistema_funcionando = False
        contacto_ficha.off()
        contacto_aux.off()
    finally:
        sistema_funcionando = False
        contacto_ficha.off()
        contacto_aux.off()
        logging.info("[INFO] Simulador de fichas apagado correctamente")
