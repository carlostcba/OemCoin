# Archivo: App/utilidades/helpers.py
import os
from configuracion.settings import PRECIO_PATH, PRECIO_DEFAULT

def leer_precio_ficha():
    """Lee el precio de la ficha desde archivo"""
    try:
        with open(PRECIO_PATH, 'r') as f:
            valor = f.read().strip()
            precio = float(valor)
            if precio <= 0:
                return PRECIO_DEFAULT
            return precio
    except FileNotFoundError:
        # Crear archivo con precio por defecto
        with open(PRECIO_PATH, 'w') as f:
            f.write(str(PRECIO_DEFAULT))
        return PRECIO_DEFAULT
    except ValueError:
        return PRECIO_DEFAULT
    except Exception:
        return PRECIO_DEFAULT