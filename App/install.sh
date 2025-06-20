#!/bin/bash

# =======================================================================
# Script de Instalación - Simulador de Fichas Virtuales V2.1 Modularizado
# Automatiza la instalación completa del sistema
# =======================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
APP_PATH="/home/oemspot/App"
SERVICE_NAME="simulador-fichas"
USER="oemspot"

print_header() {
    echo -e "${BLUE}==========================================================${NC}"
    echo -e "${BLUE}  INSTALADOR - SIMULADOR FICHAS VIRTUALES V2.1 MODULAR  ${NC}"
    echo -e "${BLUE}==========================================================${NC}"
}

print_success() {
    echo -e "${GREEN}[✓] $1${NC}"
}

print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_info() {
    echo -e "${CYAN}[i] $1${NC}"
}

check_requirements() {
    print_info "Verificando requisitos del sistema..."
    
    # Verificar que estamos en Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "Este script está diseñado para Raspberry Pi"
        echo -e "¿Continuar de todas formas? (s/N): \c"
        read -r respuesta
        if [[ ! "$respuesta" =~ ^[Ss]$ ]]; then
            print_info "Instalación cancelada"
            exit 0
        fi
    fi
    
    # Verificar Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 no está instalado"
        print_info "Instale Python 3: sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
    
    # Verificar pip
    if ! command -v pip3 >/dev/null 2>&1; then
        print_error "pip3 no está instalado"
        print_info "Instale pip3: sudo apt install python3-pip"
        exit 1
    fi
    
    # Verificar git (opcional)
    if ! command -v git >/dev/null 2>&1; then
        print_warning "Git no está instalado (opcional para actualizaciones)"
    fi
    
    print_success "Requisitos verificados"
}

create_user_and_dirs() {
    print_info "Configurando usuario y directorios..."
    
    # Crear usuario si no existe
    if ! id "$USER" >/dev/null 2>&1; then
        print_info "Creando usuario $USER..."
        sudo useradd -m -s /bin/bash "$USER"
        sudo usermod -a -G gpio,i2c,spi "$USER"
        print_success "Usuario $USER creado"
    else
        print_info "Usuario $USER ya existe"
        # Asegurar que esté en los grupos correctos
        sudo usermod -a -G gpio,i2c,spi "$USER"
    fi
    
    # Crear directorio principal
    sudo mkdir -p "$APP_PATH"
    sudo chown "$USER:$USER" "$APP_PATH"
    print_success "Directorio $APP_PATH configurado"
}

install_system_dependencies() {
    print_info "Instalando dependencias del sistema..."
    
    sudo apt update
    
    # Dependencias básicas
    sudo apt install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-tk \
        git \
        curl \
        nano \
        htop \
        bc
    
    # Dependencias para GPIO
    sudo apt install -y \
        python3-gpiozero \
        python3-rpi.gpio
    
    # Dependencias para interfaz gráfica
    sudo apt install -y \
        python3-pil \
        python3-pil.imagetk
    
    print_success "Dependencias del sistema instaladas"
}

install_python_dependencies() {
    print_info "Instalando dependencias de Python..."
    
    # Cambiar al directorio del proyecto
    cd "$APP_PATH"
    
    # Actualizar pip
    python3 -m pip install --upgrade pip
    
    # Instalar dependencias
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        print_success "Dependencias instaladas desde requirements.txt"
    else
        # Instalar dependencias básicas manualmente
        python3 -m pip install \
            mercadopago \
            gpiozero \
            RPi.GPIO \
            qrcode[pil] \
            Pillow \
            python-dotenv
        print_success "Dependencias básicas instaladas"
    fi
}

create_env_file() {
    print_info "Configurando archivo .env..."
    
    if [ ! -f "$APP_PATH/.env" ]; then
        cat > "$APP_PATH/.env" << 'EOF'
# Configuración del sistema de fichas virtuales
PUBLIC_KEY=tu_public_key_aqui
ACCESS_TOKEN=tu_access_token_aqui

# Rutas del sistema
APP_PATH=/home/oemspot/App

# Configuración GPIO
RELAY_PRODUCCION=17
RELAY_AUXILIAR=27

# Configuración del sistema
PULSO_FICHA_DURACION=1.0
PRECIO_DEFAULT=50.0
LAVADERO_ID=LAV-001
POLL_INTERVAL=3
EOF
        
        chown "$USER:$USER" "$APP_PATH/.env"
        print_success "Archivo .env creado"
        print_warning "IMPORTANTE: Configure sus claves de MercadoPago en $APP_PATH/.env"
    else
        print_info "Archivo .env ya existe"
    fi
}

install_systemd_service() {
    print_info "Instalando servicio systemd..."
    
    # Crear archivo de servicio
    sudo tee "/etc/systemd/system/$SERVICE_NAME.service" > /dev/null << EOF
[Unit]
Description=Simulador de Fichas Virtuales para Lavadero V2.1 Modular
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_PATH
ExecStart=/usr/bin/python3 $APP_PATH/main.py
Restart=always
RestartSec=10
Environment=DISPLAY=:0
Environment=PYTHONPATH=$APP_PATH

[Install]
WantedBy=multi-user.target
EOF

    # Recargar systemd
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    print_success "Servicio systemd instalado y habilitado"
}

configure_permissions() {
    print_info "Configurando permisos..."
    
    # Permisos para archivos del proyecto
    sudo chown -R "$USER:$USER" "$APP_PATH"
    sudo chmod +x "$APP_PATH/control_fichas.sh"
    
    # Permisos GPIO para el usuario
    sudo usermod -a -G gpio "$USER"
    
    # Crear regla udev para GPIO (opcional)
    sudo tee "/etc/udev/rules.d/99-gpio.rules" > /dev/null << EOF
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0664"
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c 'find -L /sys/class/gpio/ -maxdepth 2 -exec chown root:gpio {} \; -exec chmod 664 {} \; || true'"
EOF

    print_success "Permisos configurados"
}

create_default_files() {
    print_info "Creando archivos por defecto..."
    
    # Crear archivo de precio
    if [ ! -f "$APP_PATH/precio_ficha.txt" ]; then
        echo "50.0" > "$APP_PATH/precio_ficha.txt"
        chown "$USER:$USER" "$APP_PATH/precio_ficha.txt"
        print_success "Archivo precio_ficha.txt creado"
    fi
    
    # Crear directorio de pagos
    mkdir -p "$APP_PATH/pagos_fichas"
    chown "$USER:$USER" "$APP_PATH/pagos_fichas"
    
    # Crear directorio de backups
    mkdir -p "$APP_PATH/backups"
    chown "$USER:$USER" "$APP_PATH/backups"
    
    print_success "Estructura de directorios creada"
}

run_tests() {
    print_info "Ejecutando tests básicos..."
    
    cd "$APP_PATH"
    
    # Test de importación
    if sudo -u "$USER" python3 -c "
import sys
sys.path.append('$APP_PATH')
try:
    from config import *
    print('✓ Configuración cargada')
    from mercadopago_handler import mp_handler
    print('✓ MercadoPago handler inicializado')
    print('✓ Tests básicos completados')
except Exception as e:
    print(f'✗ Error en tests: {e}')
    sys.exit(1)
"; then
        print_success "Tests básicos pasados"
    else
        print_error "Falló el test básico"
        return 1
    fi
}

show_post_install_info() {
    print_header
    print_success "¡Instalación completada!"
    echo ""
    print_info "PRÓXIMOS PASOS:"
    echo ""
    echo -e "${YELLOW}1. Configurar MercadoPago:${NC}"
    echo -e "   sudo nano $APP_PATH/.env"
    echo -e "   # Editar PUBLIC_KEY y ACCESS_TOKEN"
    echo ""
    echo -e "${YELLOW}2. Iniciar el servicio:${NC}"
    echo -e "   cd $APP_PATH"
    echo -e "   ./control_fichas.sh start"
    echo ""
    echo -e "${YELLOW}3. Verificar estado:${NC}"
    echo -e "   ./control_fichas.sh status"
    echo ""
    echo -e "${YELLOW}4. Ver logs:${NC}"
    echo -e "   ./control_fichas.sh logs"
    echo ""
    echo -e "${YELLOW}5. Configurar precio:${NC}"
    echo -e "   ./control_fichas.sh precio 75.50"
    echo ""
    echo -e "${GREEN}COMANDOS ÚTILES:${NC}"
    echo -e "   ./control_fichas.sh help      # Ver ayuda completa"
    echo -e "   ./control_fichas.sh test-aux  # Test seguro auxiliar"
    echo -e "   ./control_fichas.sh stats     # Ver estadísticas"
    echo -e "   ./control_fichas.sh backup    # Crear respaldo"
    echo ""
    echo -e "${PURPLE}ARCHIVOS IMPORTANTES:${NC}"
    echo -e "   $APP_PATH/.env                    # Configuración"
    echo -e "   $APP_PATH/main.py                 # Programa principal"
    echo -e "   $APP_PATH/precio_ficha.txt        # Precio actual"
    echo -e "   $APP_PATH/simulador_fichas.log    # Logs del sistema"
    echo ""
    print_warning "RECUERDE: Configure sus claves de MercadoPago antes de usar"
}

main() {
    print_header
    
    # Verificar si se ejecuta como root para ciertas operaciones
    if [ "$EUID" -eq 0 ]; then
        print_error "No ejecute este script como root"
        print_info "Ejecute como usuario normal (usará sudo cuando sea necesario)"
        exit 1
    fi
    
    echo -e "Este script instalará el Simulador de Fichas Virtuales V2.1 Modular"
    echo -e "¿Continuar con la instalación? (s/N): \c"
    read -r respuesta
    if [[ ! "$respuesta" =~ ^[Ss]$ ]]; then
        print_info "Instalación cancelada"
        exit 0
    fi
    
    echo ""
    print_info "Iniciando instalación..."
    echo ""
    
    # Ejecutar pasos de instalación
    check_requirements
    create_user_and_dirs
    install_system_dependencies
    install_python_dependencies
    create_env_file
    install_systemd_service
    configure_permissions
    create_default_files
    
    # Tests finales
    if run_tests; then
        show_post_install_info
    else
        print_error "La instalación tuvo problemas en los tests finales"
        print_info "Revise los logs y la configuración"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"