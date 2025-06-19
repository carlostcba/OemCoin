# OemCoin Fichas Virtuales

Este repositorio contiene los scripts utilizados para controlar el sistema de "fichas" (tokens virtuales) de un lavadero de autos que funciona sobre una Raspberry Pi. El script principal es `control_fichas.sh`, el cual gestiona el servicio del simulador en Python y otras tareas de mantenimiento.

## 1. Crear el usuario `oemspot`

El simulador espera una cuenta y directorio dedicados. Créalo con:

```bash
sudo useradd -m -s /bin/bash oemspot
```

Copia la carpeta `App` desde este repositorio a `/home/oemspot/App` y asígnale la propiedad:

```bash
sudo mkdir -p /home/oemspot
sudo cp -r App /home/oemspot/
sudo chown -R oemspot:oemspot /home/oemspot/App
```

## 2. Instalar dependencias

Instala los paquetes requeridos por el simulador y el script auxiliar:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-gpiozero python3-rpi.gpio \
     python3-pil python3-tk bc jq git
sudo pip3 install mercadopago qrcode pillow
```

## 3. Configurar servicio

```bash
bash/home/oemspot/App/control_fichas.sh install-service
```

## 4. Usar `control_fichas.sh`

Todas las operaciones diarias se realizan a través del script de control. Ejecútalo como `oemspot` desde el directorio `App`:

```bash
sudo -u oemspot /home/oemspot/App/control_fichas.sh <comando>
```

Algunos comandos comunes son:

- `start` / `stop` / `restart` – gestionar el servicio del simulador  
- `status` – mostrar el estado actual del servicio y el precio configurado  
- `precio [VALOR]` – mostrar o cambiar el precio de la ficha  
- `logs` o `logs-recent N` – ver la salida de los registros  
- `backup` – crear un archivo de respaldo de los datos  
- `install-service` – instalar el servicio systemd para que el simulador se inicie automáticamente al arrancar

Ejecuta `control_fichas.sh help` para ver la lista completa de comandos.

## 5. Instalar Impresora TP80C USB

```bash
sudo apt install printer-driver-escpos

lpadmin -p TP80C -E -v usb://HPRT/TP80C?serial=TP80C023450446 -m raw

lpoptions -d TP80C
```
