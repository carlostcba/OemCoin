# Archivo: App/modelos/ficha.py
from dataclasses import dataclass
from datetime import datetime
from configuracion.settings import LAVADERO_ID, RELAY_PIN, PULSO_FICHA_DURACION

@dataclass
class FichaVirtual:
    payment_id: str
    payment_details: dict

    def to_json(self):
        return {
            "timestamp_local": datetime.now().isoformat(),
            "lavadero_id": LAVADERO_ID,
            "tipo_servicio": "ficha_virtual",
            "sistema_control": "dispositivo_analogico_existente",
            "duracion_pulso_segundos": PULSO_FICHA_DURACION,
            "modo": "standalone_polling",
            "gpio_utilizado": RELAY_PIN,
            "payment_details": self.payment_details
        }
