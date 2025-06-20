# Archivo: App/simulador.py
import threading
from utilidades.logger import logger
from interfaz.display import loop_display
from servicios.monitoreo import bucle_monitoreo

def main():
    logger.info("[INIT] Iniciando simulador modularizado")
    
    # Iniciar threads paralelos
    thread_monitor = threading.Thread(target=bucle_monitoreo, daemon=True)
    thread_display = threading.Thread(target=loop_display, daemon=True)

    thread_monitor.start()
    thread_display.start()

    thread_monitor.join()
    thread_display.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("[SALIDA] Finalizando simulador")
