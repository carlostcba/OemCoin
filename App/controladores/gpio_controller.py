# Archivo: App/controladores/gpio_controller.py
from gpiozero import OutputDevice
from configuracion.settings import RELAY_PIN, RELAY_PIN_AUX
from utilidades.logger import logger

class GPIOController:
    def __init__(self):
        self.prod = OutputDevice(RELAY_PIN, active_high=True, initial_value=False)
        self.aux = OutputDevice(RELAY_PIN_AUX, active_high=True, initial_value=False)
        self.apagar_todos()

    def activar(self, pin, duracion=1.0):
        rele = self._get_rele(pin)
        if not rele:
            logger.error(f"[GPIO] GPIO {pin} no válido")
            return False

        logger.info(f"[GPIO] Activando GPIO {pin} por {duracion} segundos")
        rele.on()
        from time import sleep
        sleep(duracion)
        rele.off()
        return True

    def apagar_todos(self):
        self.prod.off()
        self.aux.off()
        logger.info("[GPIO] Todos los relés apagados")

    def _get_rele(self, pin):
        if pin == RELAY_PIN:
            return self.prod
        elif pin == RELAY_PIN_AUX:
            return self.aux
        else:
            return None
