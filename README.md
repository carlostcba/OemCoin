# Simulador de Fichas Virtuales para Lavadero V2.1 - Modularizado

Sistema completo para reemplazar fichas físicas por pagos digitales con MercadoPago en lavaderos existentes.

## 🚀 Características Principales

- **Pagos Digitales**: Integración completa con MercadoPago
- **Interfaz Moderna**: Diseño estilo MercadoPago en pantalla
- **Sin Modificaciones**: Se conecta al sistema analógico existente
- **Información Detallada**: Datos completos del cliente y transacción
- **Seguridad**: Solo conexiones de salida, sin puertos abiertos
- **Modular**: Código organizado en módulos especializados

## 📁 Estructura del Proyecto

```
/home/oemspot/App/
├── .env                     # Variables de configuración
├── main.py                  # Coordinador principal
├── config.py                # Configuración del sistema
├── hardware.py              # Control de relés y GPIO
├── mercadopago_handler.py   # Integración con MercadoPago
├── file_manager.py          # Manejo de archivos
├── payment_monitor.py       # Monitor de pagos
├── gui_interface.py         # Interfaz gráfica
├── requirements.txt         # Dependencias
├── README.md               # Documentación
├── control_fichas.sh       # Script de control (existente)
├── pagos_fichas/           # Registros de pagos
├── precio_ficha.txt        # Precio actual
└── simulador_fichas.log    # Logs del sistema
```

## ⚙️ Configuración Inicial

### 1. Instalar Dependencias
```bash
cd /home/oemspot/App
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno
Editar el archivo `.env`:
```bash
# Claves de MercadoPago
PUBLIC_KEY=AAPP_USR-tu-public-key
ACCESS_TOKEN=APP_USR-tu-access-token

# Configuración del sistema
APP_PATH=/home/oemspot/App
RELAY_PRODUCCION=17
RELAY_AUXILIAR=27
PULSO_FICHA_DURACION=1.0
PRECIO_DEFAULT=1.0
LAVADERO_ID=LAV-001
POLL_INTERVAL=3
```

### 3. Ejecutar el Sistema
```bash
python3 main.py
```

## 🔧 Módulos del Sistema

### `config.py`
- Carga variables de entorno desde `.env`
- Define rutas y configuraciones del sistema
- Crea directorios necesarios

### `hardware.py`
- Control seguro de relés GPIO
- Simulación de inserción de fichas
- Tests manuales de contactos

### `mercadopago_handler.py`
- Integración con SDK de MercadoPago
- Generación de códigos QR
- Consulta y procesamiento de pagos

### `file_manager.py`
- Manejo de precios y configuración
- Persistencia de datos de pagos
- Registros de transacciones

### `payment_monitor.py`
- Monitoreo en tiempo real de pagos
- Validación de transacciones
- Control de estado del sistema

### `gui_interface.py`
- Interfaz gráfica estilo MercadoPago
- Visualización de códigos QR
- Información detallada de pagos

### `main.py`
- Coordinador principal del sistema
- Inicialización de módulos
- Manejo de errores y cleanup

## 🎛️ Control del Sistema

### Usar el Script de Control Existente
```bash
# Iniciar el simulador
./control_fichas.sh start

# Ver estado
./control_fichas.sh status

# Ver logs en tiempo real
./control_fichas.sh logs

# Cambiar precio
./control_fichas.sh precio 75.50

# Test manual seguro (auxiliar)
./control_fichas.sh test-aux

# Test de producción (requiere confirmación)
./control_fichas.sh test-prod
```

### Tests Manuales desde Python
```python
from hardware import hardware

# Test auxiliar (seguro)
hardware.activar_rele_manual(27, 1.0)

# Test producción (solo con confirmación)
hardware.activar_rele_manual(17, 1.0)
```

## 🔍 Monitoreo y Logs

### Ver Logs del Sistema
```bash
tail -f /home/oemspot/App/simulador_fichas.log
```

### Archivos de Pago
Los pagos se guardan en `pagos_fichas/` con formato:
```
YYYYMMDD_HHMMSS_payment_id.json
```

Cada archivo contiene información completa del pago y cliente.

## 🔒 Seguridad

- **Relé de Producción (GPIO 17)**: Solo se activa con pagos confirmados
- **Relé Auxiliar (GPIO 27)**: Para tests manuales seguros
- **Sin Tests Automáticos**: No hay activaciones automáticas al iniciar
- **Validación de Pagos**: Solo procesa pagos posteriores