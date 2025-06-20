# -*- coding: utf-8 -*-
"""
Interfaz gráfica del simulador de fichas estilo MercadoPago
"""
import os
import time
import logging
import threading
import qrcode
from PIL import Image, ImageTk
from config import QR_TEMP_PATH
from mercadopago_handler import mp_handler
from file_manager import file_manager
from payment_monitor import pago_recibido, ultimo_pago_info, lock, sistema_funcionando
from hardware import ficha_activada

# Verificar entorno gráfico
if os.environ.get("DISPLAY"):
    import tkinter as tk
    from tkinter import ttk
else:
    print("[!] No se detectó entorno gráfico. No se mostrará QR en pantalla HDMI.")

class GUIInterface:
    def __init__(self):
        self.root = None
        self.precio_actual = file_manager.leer_precio_ficha()
        self.qr_link_actual = None
        self.preference_id_actual = None
        self.tk_img = None
        
        # Referencias a widgets para actualización
        self.precio_label = None
        self.estado_label = None
        self.qr_label = None
        self.pago_info_frame = None
        
    def generar_qr_interface(self):
        """Genera QR para la interfaz"""
        link, preference_id = mp_handler.generar_qr_ficha(self.precio_actual)
        self.qr_link_actual = link
        self.preference_id_actual = preference_id
        
        # Generar imagen QR
        qr = qrcode.make(self.qr_link_actual)
        qr.save(QR_TEMP_PATH)
        
        return self.qr_link_actual
    
    def mostrar_interfaz_simulador(self):
        """Interfaz gráfica del simulador de fichas estilo MercadoPago"""
        # Inicializar
        self.generar_qr_interface()
        
        if not os.environ.get("DISPLAY"):
            logging.info("[INFO] Sin entorno gráfico - funcionando en modo consola")
            while sistema_funcionando:
                time.sleep(1)
            return

        self.root = tk.Tk()
        self.root.title("Lavadero - Pago con MercadoPago")
        self.root.configure(bg='#00A0E6')  # Azul MercadoPago
        
        self._crear_interfaz()
        self._iniciar_actualizacion_interfaz()
        
        # Configurar pantalla completa
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self._cerrar_simulador())
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', False))
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._cerrar_simulador()
    
    def _crear_interfaz(self):
        """Crea los elementos de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#00A0E6')
        main_frame.pack(expand=True, fill='both', padx=40, pady=30)
        
        # Header con logo MercadoPago simulado
        self._crear_header(main_frame)
        
        # Container principal blanco
        container = tk.Frame(main_frame, bg='#ededed', relief='flat', bd=0)
        container.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Padding interno
        content_frame = tk.Frame(container, bg='#ededed')
        content_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Crear elementos del contenido
        self._crear_precio(content_frame)
        self._crear_qr(content_frame)
        self._crear_instrucciones(content_frame)
        self._crear_estado(content_frame)
        self._crear_info_pago(content_frame)
        self._crear_footer(main_frame)
    
    def _crear_header(self, parent):
        """Crea el header de la interfaz"""
        header_frame = tk.Frame(parent, bg='#00A0E6')
        header_frame.pack(fill='x', pady=(0, 20))
        
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
            text="Ficha Virtual - Lavadero Automático",
            font=("Roboto", 18),
            fg='#E3F2FD',
            bg='#00A0E6'
        )
        subtitle_label.pack(pady=(5, 0))
    
    def _crear_precio(self, parent):
        """Crea la sección de precio"""
        precio_frame = tk.Frame(parent, bg='#ededed')
        precio_frame.pack(fill='x', pady=(0, 30))
        
        self.precio_label = tk.Label(
            precio_frame,
            text=f"${self.precio_actual:.0f}",
            font=("Roboto", 48, "bold"),
            fg='#00A0E6',
            bg='#ededed'
        )
        self.precio_label.pack()
        
        desc_precio = tk.Label(
            precio_frame,
            text="Precio por ficha virtual",
            font=("Roboto", 16),
            fg='#666666',
            bg='#ededed'
        )
        desc_precio.pack()
    
    def _crear_qr(self, parent):
        """Crea la sección del código QR"""
        qr_frame = tk.Frame(parent, bg='#ededed')
        qr_frame.pack(pady=20)
        
        qr_container = tk.Frame(qr_frame, bg='#F5F5F5', relief='solid', bd=1)
        qr_container.pack(padx=20, pady=20)
        
        img = Image.open(QR_TEMP_PATH)
        img = img.resize((300, 300), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img)
        self.qr_label = tk.Label(qr_container, image=self.tk_img, bg='#F5F5F5')
        self.qr_label.pack(padx=15, pady=15)
    
    def _crear_instrucciones(self, parent):
        """Crea las instrucciones de uso"""
        instruc_label = tk.Label(
            parent,
            text="1. Escanee el código QR con su celular\n2. Complete el pago en la app de MercadoPago\n3. El lavado se activará automáticamente",
            font=("Roboto", 16),
            fg='#333333',
            bg='#ededed',
            justify='center'
        )
        instruc_label.pack(pady=(20, 30))
    
    def _crear_estado(self, parent):
        """Crea la sección de estado"""
        estado_frame = tk.Frame(parent, bg='#ededed')
        estado_frame.pack(fill='x', pady=20)
        
        self.estado_label = tk.Label(
            estado_frame,
            text="Esperando el pago...",
            font=("Roboto", 20, "bold"),
            fg='#00a0e6',
            bg='#ededed'
        )
        self.estado_label.pack()
    
    def _crear_info_pago(self, parent):
        """Crea el frame para información del pago (inicialmente oculto)"""
        self.pago_info_frame = tk.Frame(parent, bg='#E8F5E8', relief='solid', bd=1)
    
    def _crear_footer(self, parent):
        """Crea el footer de la interfaz"""
        tech_frame = tk.Frame(parent, bg='#00A0E6')
        tech_frame.pack(fill='x', pady=(10, 0))
        
        tech_label = tk.Label(
            tech_frame,
            text="Copyright 2025 OemCoin",
            font=("Roboto", 12),
            fg='#B3E5FC',
            bg='#00A0E6'
        )
        tech_label.pack()
    
    def _mostrar_info_pago(self):
        """Muestra la información del pago recibido"""
        if ultimo_pago_info:
            # Limpiar frame anterior
            for widget in self.pago_info_frame.winfo_children():
                widget.destroy()
            
            # Título del pago
            titulo_pago = tk.Label(
                self.pago_info_frame,
                text="¡PAGO RECIBIDO!",
                font=("Roboto", 24, "bold"),
                fg='#2E7D32',
                bg='#E8F5E8'
            )
            titulo_pago.pack(pady=(15, 10))
            
            # Monto
            monto = ultimo_pago_info.get("transaction_amount", 0)
            monto_label = tk.Label(
                self.pago_info_frame,
                text=f"${monto:.2f} ARS",
                font=("Roboto", 32, "bold"),
                fg='#1B5E20',
                bg='#E8F5E8'
            )
            monto_label.pack(pady=5)
            
            # Información del cliente
            self._mostrar_info_cliente()
            
            # Mostrar el frame
            self.pago_info_frame.pack(fill='x', pady=20)
    
    def _mostrar_info_cliente(self):
        """Muestra la información del cliente en el pago"""
        payer = ultimo_pago_info.get("payer", {})
        nombre_completo = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
        
        if nombre_completo:
            cliente_label = tk.Label(
                self.pago_info_frame,
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
                self.pago_info_frame,
                text=f"Email: {email}",
                font=("Roboto", 14),
                fg='#388E3C',
                bg='#E8F5E8'
            )
            email_label.pack(pady=2)
        
        # Método de pago
        card = ultimo_pago_info.get("card", {})
        if card:
            tarjeta_info = f"Tarjeta: ****{card.get('last_four_digits', '')}"
            tarjeta_label = tk.Label(
                self.pago_info_frame,
                text=tarjeta_info,
                font=("Roboto", 14),
                fg='#388E3C',
                bg='#E8F5E8'
            )
            tarjeta_label.pack(pady=2)
        
        # ID de transacción
        payment_id = str(ultimo_pago_info.get("id", ""))[:20]
        id_label = tk.Label(
            self.pago_info_frame,
            text=f"ID: {payment_id}...",
            font=("Roboto", 12),
            fg='#666666',
            bg='#E8F5E8'
        )
        id_label.pack(pady=(10, 15))
    
    def _actualizar_interfaz_simulador(self):
        """Actualiza la interfaz según el estado"""
        while sistema_funcionando and self.root:
            try:
                if pago_recibido.is_set():
                    # Pago recibido - mostrar información
                    self.estado_label.config(
                        text="Activando lavadero...",
                        fg='#2E7D32'
                    )
                    self.precio_label.config(fg='#2E7D32')
                    
                    # Mostrar información del pago
                    self._mostrar_info_pago()
                    
                    # Esperar un poco y luego resetear
                    time.sleep(8)
                    pago_recibido.clear()
                    
                    # Ocultar info del pago y volver al estado normal
                    self.pago_info_frame.pack_forget()
                    self.estado_label.config(
                        text="Esperando el pago...",
                        fg='#00a0e6'
                    )
                    self.precio_label.config(fg='#00A0E6')
                    
                elif ficha_activada.is_set():
                    # Ficha siendo activada
                    self.estado_label.config(
                        text="Activando ficha virtual...",
                        fg='#00a0e6'
                    )
                    
                else:
                    # Estado normal - actualizar precio si cambió
                    nuevo_precio = file_manager.leer_precio_ficha()
                    if nuevo_precio != self.precio_actual:
                        with lock:
                            self.precio_actual = nuevo_precio
                            self.precio_label.config(text=f"${self.precio_actual:.0f}")
                            # Regenerar QR con nuevo precio
                            self.generar_qr_interface()
                            # Actualizar imagen QR
                            img = Image.open(QR_TEMP_PATH)
                            img = img.resize((300, 300), Image.LANCZOS)
                            self.tk_img = ImageTk.PhotoImage(img)
                            self.qr_label.config(image=self.tk_img)
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"[ERROR] Error actualizando interfaz: {e}")
                time.sleep(1)
    
    def _iniciar_actualizacion_interfaz(self):
        """Inicia el hilo de actualización de la interfaz"""
        threading.Thread(target=self._actualizar_interfaz_simulador, daemon=True).start()
    
    def _cerrar_simulador(self):
        """Cierra el simulador de manera segura"""
        global sistema_funcionando
        sistema_funcionando = False
        from hardware import hardware
        hardware.apagar_relais()
        if self.root:
            self.root.quit()

# Instancia global de la interfaz
gui_interface = GUIInterface()