#!/bin/bash

# =======================================================================
# Script de Control para Simulador de Fichas Virtuales - V2.1 Actualizado
# Facilita la administracion del sistema de lavadero con fichas digitales
# ACTUALIZADO: Sin tests automaticos, rele auxiliar manual solamente
# =======================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuracion
SERVICE_NAME="simulador-fichas"
APP_PATH="/home/oemspot/App"
PRECIO_FILE="$APP_PATH/precio_ficha.txt"
LOG_FILE="$APP_PATH/simulador_fichas.log"
PAGOS_DIR="$APP_PATH/pagos_fichas"
SCRIPT_PATH="$APP_PATH/main.py"

# GPIOs
GPIO_PRODUCCION=17
GPIO_AUXILIAR=27

# Funciones de utilidad
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  CONTROL DE FICHAS VIRTUALES - LAVADERO V2.1  ${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo -e "${CYAN}?? Interfaz MercadoPago � ?? Rele Auxiliar Manual${NC}"
}

print_success() {
    echo -e "${GREEN}[?] $1${NC}"
}

print_error() {
    echo -e "${RED}[?] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_info() {
    echo -e "${CYAN}[i] $1${NC}"
}

# Verificar si el sistema esta instalado
check_installation() {
    if [ ! -f "$SCRIPT_PATH" ]; then
        print_error "Simulador no encontrado en $SCRIPT_PATH"
        echo "Instale primero el sistema de fichas virtuales"
        exit 1
    fi
    
    if [ ! -f "$PRECIO_FILE" ]; then
        print_warning "Archivo de precio no encontrado, creando..."
        echo "1.0" > "$PRECIO_FILE"
        print_success "Archivo de precio creado con valor por defecto: \$50"
    fi
}

# Funcion para mostrar el estado del servicio
show_status() {
    echo -e "\n${PURPLE}=== ESTADO DEL SISTEMA V2.1 ===${NC}"
    
    # Estado del servicio
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Servicio: ACTIVO"
    else
        print_error "Servicio: INACTIVO"
    fi
    
    # Precio actual
    if [ -f "$PRECIO_FILE" ]; then
        PRECIO=$(cat "$PRECIO_FILE" 2>/dev/null || echo "ERROR")
        print_info "Precio actual: \$${PRECIO}"
    else
        print_error "Archivo de precio no encontrado"
    fi
    
    # Informacion de GPIOs
    print_info "GPIO Produccion: $GPIO_PRODUCCION (solo pagos)"
    print_info "GPIO Auxiliar: $GPIO_AUXILIAR (uso manual)"
    
    # Estadisticas del dia
    local fichas_hoy=$(count_fichas_today)
    print_info "Fichas procesadas hoy: $fichas_hoy"
    
    # Ultimo pago procesado
    if [ -d "$PAGOS_DIR" ]; then
        local ultimo_archivo=$(ls -t "$PAGOS_DIR"/*.json 2>/dev/null | head -1)
        if [ ! -z "$ultimo_archivo" ]; then
            local fecha_archivo=$(basename "$ultimo_archivo" | cut -d'_' -f1)
            local fecha_formateada=$(echo "$fecha_archivo" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3/')
            print_info "Ultimo pago: $fecha_formateada"
        fi
    fi
    
    # Ultimo archivo de log
    if [ -f "$LOG_FILE" ]; then
        local ultima_linea=$(tail -1 "$LOG_FILE" 2>/dev/null)
        if [ ! -z "$ultima_linea" ]; then
            print_info "Ultimo log: ${ultima_linea:0:80}..."
        fi
    fi
    
    echo ""
}

# Contar fichas procesadas hoy
count_fichas_today() {
    local fecha_hoy=$(date +%Y%m%d)
    if [ -d "$PAGOS_DIR" ]; then
        ls "$PAGOS_DIR"/${fecha_hoy}*.json 2>/dev/null | wc -l
    else
        echo "0"
    fi
}

# Iniciar el servicio
start_service() {
    echo -e "\n${GREEN}?? Iniciando simulador de fichas V2.1...${NC}"
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_warning "El servicio ya esta en ejecucion"
        return 0
    fi
    
    sudo systemctl start $SERVICE_NAME
    sleep 3
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Simulador iniciado correctamente"
        print_info "Interfaz MercadoPago disponible en pantalla"
        print_info "Sin tests automaticos - solo activacion por pagos"
        print_info "Use 'logs' para ver la actividad en tiempo real"
    else
        print_error "Error al iniciar el simulador"
        print_info "Use 'logs' para ver los errores"
        return 1
    fi
}

# Detener el servicio
stop_service() {
    echo -e "\n${RED}? Deteniendo simulador de fichas...${NC}"
    
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        print_warning "El servicio ya esta detenido"
        return 0
    fi
    
    sudo systemctl stop $SERVICE_NAME
    sleep 2
    
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Simulador detenido correctamente"
    else
        print_error "Error al detener el simulador"
        return 1
    fi
}

# Reiniciar el servicio
restart_service() {
    echo -e "\n${YELLOW}?? Reiniciando simulador de fichas...${NC}"
    
    sudo systemctl restart $SERVICE_NAME
    sleep 3
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Simulador reiniciado correctamente"
        print_info "Interfaz MercadoPago actualizada"
        print_info "Sistema listo sin tests automaticos"
    else
        print_error "Error al reiniciar el simulador"
        return 1
    fi
}

# Mostrar logs en tiempo real
show_logs() {
    echo -e "\n${CYAN}?? Logs en tiempo real (Ctrl+C para salir):${NC}"
    echo -e "${YELLOW}============================================${NC}"
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        print_error "Archivo de log no encontrado: $LOG_FILE"
        print_info "�Esta el simulador en ejecucion?"
    fi
}

# Mostrar ultimas lineas del log
show_recent_logs() {
    local lines=${1:-20}
    echo -e "\n${CYAN}?? Ultimas $lines lineas del log:${NC}"
    echo -e "${YELLOW}================================${NC}"
    
    if [ -f "$LOG_FILE" ]; then
        tail -n $lines "$LOG_FILE"
    else
        print_error "Archivo de log no encontrado"
    fi
}

# Gestionar precio
manage_price() {
    local nuevo_precio=$1
    
    if [ -z "$nuevo_precio" ]; then
        # Mostrar precio actual
        if [ -f "$PRECIO_FILE" ]; then
            local precio_actual=$(cat "$PRECIO_FILE")
            echo -e "\n${GREEN}?? Precio actual: \$${precio_actual}${NC}"
        else
            print_error "Archivo de precio no encontrado"
        fi
    else
        # Validar que es un numero
        if ! [[ "$nuevo_precio" =~ ^[0-9]+\.?[0-9]*$ ]]; then
            print_error "El precio debe ser un numero valido (ej: 1.0 o 75)"
            return 1
        fi
        
        # Actualizar precio
        echo "$nuevo_precio" > "$PRECIO_FILE"
        
        if [ $? -eq 0 ]; then
            print_success "Precio actualizado a: \$${nuevo_precio}"
            print_info "El cambio se aplicara en los proximos 15 segundos"
            print_info "La interfaz MercadoPago se actualizara automaticamente"
        else
            print_error "Error al actualizar el precio"
            return 1
        fi
    fi
}

# Test manual de contacto usando Python - ACTUALIZADO PARA V2.1
test_contacto_manual() {
    local tipo=${1:-"auxiliar"}
    local duracion=${2:-1.0}
    
    if [ "$tipo" = "auxiliar" ] || [ "$tipo" = "aux" ]; then
        local gpio=$GPIO_AUXILIAR
        local descripcion="AUXILIAR (GPIO $gpio)"
        local color="${YELLOW}"
        local confirmacion_requerida="simple"
    elif [ "$tipo" = "prod" ] || [ "$tipo" = "produccion" ]; then
        local gpio=$GPIO_PRODUCCION
        local descripcion="PRODUCCION (GPIO $gpio)"
        local color="${RED}"
        local confirmacion_requerida="estricta"
    else
        print_error "Tipo invalido. Use: auxiliar o prod"
        return 1
    fi
    
    echo -e "\n${color}?? Probando contacto $descripcion por ${duracion}s...${NC}"
    print_warning "ATENCION: Esto activara el contacto manualmente"
    
    if [ "$confirmacion_requerida" = "estricta" ]; then
        print_warning "??  CUIDADO: Esto activara el sistema de PRODUCCION"
        print_warning "??  Solo use esto si esta seguro de lo que hace"
        echo -e "�Esta ABSOLUTAMENTE seguro? (escriba 'SI ESTOY SEGURO'): \c"
        read -r confirmacion
        if [ "$confirmacion" != "SI ESTOY SEGURO" ]; then
            print_info "Test de produccion cancelado"
            return 0
        fi
    else
        echo -e "�Continuar con test auxiliar? (s/N): \c"
        read -r confirmacion
        if [[ ! "$confirmacion" =~ ^[Ss]$ ]]; then
            print_info "Test cancelado"
            return 0
        fi
    fi
    
    # Usar la funcion Python del simulador
    python3 -c "
import sys
sys.path.append('$APP_PATH')

try:
    # Importar la funcion del simulador
    import os
    os.chdir('$APP_PATH')
    
    from gpiozero import OutputDevice
    import time
    
    print('?? Configurando GPIO $gpio...')
    
    if $gpio == $GPIO_PRODUCCION:
        contacto = OutputDevice($gpio, active_high=True, initial_value=False)
        tipo_desc = 'PRODUCCION'
    else:
        contacto = OutputDevice($gpio, active_high=True, initial_value=False)
        tipo_desc = 'AUXILIAR'
    
    print(f'? Activando contacto {tipo_desc} (GPIO $gpio)...')
    contacto.on()
    
    # Countdown visual
    for i in range(int($duracion), 0, -1):
        print(f'   Contacto ACTIVO - {i} segundos restantes')
        time.sleep(1)
    
    contacto.off()
    print(f'? Test completado - Contacto {tipo_desc} desactivado')
    
except Exception as e:
    print(f'? Error en test: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Test de contacto $descripcion completado exitosamente"
        if [ "$tipo" = "auxiliar" ]; then
            print_info "El contacto auxiliar se uso para pruebas sin afectar produccion"
        fi
    else
        print_error "Error durante el test del contacto"
    fi
}

# Estadisticas detalladas - ACTUALIZADO
show_stats() {
    echo -e "\n${PURPLE}?? ESTADISTICAS DETALLADAS V2.1${NC}"
    echo -e "${PURPLE}=================================${NC}"
    
    # Estadisticas generales
    if [ -d "$PAGOS_DIR" ]; then
        local total_fichas=$(ls "$PAGOS_DIR"/*.json 2>/dev/null | wc -l)
        local fichas_hoy=$(count_fichas_today)
        local fichas_ayer=$(ls "$PAGOS_DIR"/$(date -d yesterday +%Y%m%d)*.json 2>/dev/null | wc -l)
        
        echo -e "Total fichas procesadas: ${GREEN}$total_fichas${NC}"
        echo -e "Fichas hoy:              ${GREEN}$fichas_hoy${NC}"
        echo -e "Fichas ayer:             ${GREEN}$fichas_ayer${NC}"
        
        # Calcular ingresos del dia
        local ingresos_hoy=0
        if [ $fichas_hoy -gt 0 ]; then
            local precio_actual=$(cat "$PRECIO_FILE" 2>/dev/null || echo "50")
            ingresos_hoy=$(echo "$fichas_hoy * $precio_actual" | bc 2>/dev/null || echo "N/A")
            echo -e "Ingresos hoy:            ${GREEN}\$${ingresos_hoy}${NC}"
        fi
        
        # Ultimas 5 transacciones con mas detalles
        echo -e "\n${CYAN}Ultimas 5 transacciones:${NC}"
        local archivos=($(ls -t "$PAGOS_DIR"/*.json 2>/dev/null | head -5))
        
        if [ ${#archivos[@]} -gt 0 ]; then
            for archivo in "${archivos[@]}"; do
                local timestamp=$(basename "$archivo" | cut -d'_' -f1)
                local fecha_hora=$(echo "$timestamp" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
                
                # Intentar extraer monto del JSON
                local monto=$(grep -o '"transaction_amount":[0-9.]*' "$archivo" 2>/dev/null | cut -d':' -f2 || echo "N/A")
                
                echo "  ?? $fecha_hora - \$${monto}"
            done
        else
            echo "  No hay transacciones registradas"
        fi
        
        # Informacion de configuracion V2.1
        echo -e "\n${CYAN}Configuracion del sistema V2.1:${NC}"
        echo -e "GPIO Produccion:         ${GREEN}$GPIO_PRODUCCION${NC} (solo pagos)"
        echo -e "GPIO Auxiliar:           ${GREEN}$GPIO_AUXILIAR${NC} (uso manual)"
        echo -e "Tests automaticos:       ${YELLOW}DESHABILITADOS${NC}"
        echo -e "Modo de operacion:       ${GREEN}Solo pagos reales${NC}"
        
    else
        print_warning "Directorio de pagos no encontrado"
    fi
    
    # Espacio en disco
    local espacio_libre=$(df -h "$APP_PATH" | awk 'NR==2 {print $4}')
    echo -e "\nEspacio libre:           ${GREEN}$espacio_libre${NC}"
    
    # Uptime del sistema
    local uptime_info=$(uptime -p)
    echo -e "Tiempo encendido:        ${GREEN}$uptime_info${NC}"
    
    # Temperatura del Pi (si esta disponible)
    if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
        local temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        local temp_celsius=$((temp / 1000))
        echo -e "Temperatura CPU:         ${GREEN}${temp_celsius}�C${NC}"
    fi
}

# Mostrar informacion de pagos recientes
show_recent_payments() {
    local count=${1:-10}
    
    echo -e "\n${CYAN}?? Ultimos $count pagos procesados:${NC}"
    echo -e "${YELLOW}====================================${NC}"
    
    if [ -d "$PAGOS_DIR" ]; then
        local archivos=($(ls -t "$PAGOS_DIR"/*.json 2>/dev/null | head $count))
        
        if [ ${#archivos[@]} -gt 0 ]; then
            for archivo in "${archivos[@]}"; do
                echo -e "\n${GREEN}?? $(basename "$archivo")${NC}"
                
                # Extraer informacion relevante del JSON
                if command -v jq >/dev/null 2>&1; then
                    # Si jq esta disponible, usar para parsear JSON
                    local monto=$(jq -r '.payment_details.transaction_amount // "N/A"' "$archivo" 2>/dev/null)
                    local email=$(jq -r '.payment_details.payer.email // "N/A"' "$archivo" 2>/dev/null)
                    local metodo=$(jq -r '.payment_details.payment_method.id // "N/A"' "$archivo" 2>/dev/null)
                    
                    echo "  ?? Monto: \$${monto}"
                    echo "  ?? Email: ${email}"
                    echo "  ?? Metodo: ${metodo}"
                else
                    # Parseo basico sin jq
                    local monto=$(grep -o '"transaction_amount":[0-9.]*' "$archivo" | cut -d':' -f2 || echo "N/A")
                    echo "  ?? Monto: \$${monto}"
                fi
            done
        else
            echo "  No hay pagos registrados"
        fi
    else
        print_error "Directorio de pagos no encontrado"
    fi
}

# Respaldar datos - ACTUALIZADO
backup_data() {
    local fecha=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/home/oemspot/App/backups"
    local backup_file="$backup_dir/fichas_backup_v21_$fecha.tar.gz"
    
    echo -e "\n${BLUE}?? Creando respaldo V2.1...${NC}"
    
    # Crear directorio de backup
    mkdir -p "$backup_dir"
    
    # Crear backup
    tar -czf "$backup_file" -C "$APP_PATH" \
        pagos_fichas/ \
        precio_ficha.txt \
        simulador_fichas.log \
        qr_ficha.png \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup creado: $backup_file ($size)"
        
        # Informacion del backup
        local num_pagos=$(tar -tzf "$backup_file" | grep "pagos_fichas.*\.json" | wc -l)
        print_info "Archivos de pagos incluidos: $num_pagos"
        
        # Limpiar backups antiguos (mantener ultimos 5)
        ls -t "$backup_dir"/fichas_backup_*.tar.gz | tail -n +6 | xargs rm -f 2>/dev/null
        print_info "Backups antiguos limpiados (mantenidos ultimos 5)"
    else
        print_error "Error al crear el backup"
    fi
}

# Instalacion del servicio systemd - ACTUALIZADO PARA V2.1
install_service() {
    echo -e "\n${BLUE}?? Instalando servicio systemd V2.1...${NC}"
    
    local service_file="/etc/systemd/system/$SERVICE_NAME.service"
    
    # Crear archivo de servicio
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=Simulador de Fichas Virtuales para Lavadero V2.1
After=network.target

[Service]
Type=simple
User=oemspot
Group=oemspot
WorkingDirectory=$APP_PATH
ExecStart=/usr/bin/python3 $SCRIPT_PATH
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

    if [ $? -eq 0 ]; then
        print_success "Archivo de servicio V2.1 creado"
        
        # Recargar systemd y habilitar servicio
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
        
        print_success "Servicio instalado y habilitado"
        print_info "Caracteristicas V2.1:"
        print_info "  � Sin tests automaticos al iniciar"
        print_info "  � GPIO $GPIO_PRODUCCION solo para pagos reales"
        print_info "  � GPIO $GPIO_AUXILIAR para uso manual"
        print_info "  � Interfaz estilo MercadoPago"
        print_info "  � Informacion detallada de pagos"
        print_info "Use 'start' para iniciar el servicio"
    else
        print_error "Error al crear el archivo de servicio"
    fi
}

# Funcion de ayuda - ACTUALIZADA PARA V2.1
show_help() {
    print_header
    echo -e "\n${CYAN}COMANDOS DISPONIBLES V2.1:${NC}"
    echo ""
    echo -e "${GREEN}Gestion del Servicio:${NC}"
    echo -e "  start             Iniciar el simulador de fichas"
    echo -e "  stop              Detener el simulador"
    echo -e "  restart           Reiniciar el simulador"
    echo -e "  status            Mostrar estado del sistema"
    echo ""
    echo -e "${GREEN}Configuracion:${NC}"
    echo -e "  precio [VALOR]    Mostrar o cambiar precio de ficha"
    echo -e "  install-service   Instalar servicio systemd V2.1"
    echo ""
    echo -e "${GREEN}Monitoreo:${NC}"
    echo -e "  logs              Ver logs en tiempo real"
    echo -e "  logs-recent [N]   Ver ultimas N lineas del log (default: 20)"
    echo -e "  stats             Mostrar estadisticas detalladas"
    echo -e "  pagos [N]         Ver ultimos N pagos (default: 10)"
    echo ""
    echo -e "${GREEN}Pruebas Manuales - V2.1:${NC}"
    echo -e "  test-aux [SEG]    Probar contacto AUXILIAR (GPIO $GPIO_AUXILIAR)"
    echo -e "  test-prod [SEG]   Probar contacto PRODUCCION (GPIO $GPIO_PRODUCCION)"
    echo -e "  fichas-hoy        Contar fichas procesadas hoy"
    echo ""
    echo -e "${GREEN}Mantenimiento:${NC}"
    echo -e "  backup            Crear respaldo de datos"
    echo -e "  help              Mostrar esta ayuda"
    echo ""
    echo -e "${YELLOW}EJEMPLOS V2.1:${NC}"
    echo -e "  $0 precio 75.50        # Cambiar precio a \$75.50"
    echo -e "  $0 test-aux            # Test seguro auxiliar (1 seg)"
    echo -e "  $0 test-aux 3          # Test auxiliar por 3 segundos"
    echo -e "  $0 test-prod 2         # Test produccion por 2 segundos"
    echo -e "  $0 pagos 5             # Ver ultimos 5 pagos"
    echo -e "  $0 logs-recent 50      # Ver ultimas 50 lineas del log"
    echo ""
    echo -e "${PURPLE}NOVEDADES V2.1:${NC}"
    echo -e "  ?? Sin tests automaticos al iniciar"
    echo -e "  ?? GPIO $GPIO_PRODUCCION solo activa con pagos reales"
    echo -e "  ?? GPIO $GPIO_AUXILIAR para tests manuales seguros"
    echo -e "  ?? Interfaz estilo MercadoPago"
    echo -e "  ?? Informacion detallada de clientes y pagos"
    echo ""
    echo -e "${RED}IMPORTANTE V2.1:${NC}"
    echo -e "  � El contacto de produccion SOLO se activa con pagos"
    echo -e "  � Use test-aux para pruebas seguras"
    echo -e "  � test-prod requiere confirmacion estricta"
    echo ""
}

# Funcion principal - ACTUALIZADA
main() {
    # Verificar instalacion
    check_installation
    
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        logs-recent)
            show_recent_logs "$2"
            ;;
        precio)
            manage_price "$2"
            ;;
        test-aux|test-auxiliar)
            test_contacto_manual "auxiliar" "$2"
            ;;
        test-prod|test-produccion)
            test_contacto_manual "prod" "$2"
            ;;
        fichas-hoy)
            local fichas=$(count_fichas_today)
            local precio=$(cat "$PRECIO_FILE" 2>/dev/null || echo "50")
            local ingresos=$(echo "$fichas * $precio" | bc 2>/dev/null || echo "N/A")
            echo -e "${GREEN}Fichas virtuales procesadas hoy: $fichas${NC}"
            echo -e "${GREEN}Ingresos estimados hoy: \$${ingresos}${NC}"
            ;;
        stats)
            show_stats
            ;;
        pagos)
            show_recent_payments "$2"
            ;;
        backup)
            backup_data
            ;;
        install-service)
            install_service
            ;;
        help|--help|-h)
            show_help
            ;;
        # Compatibilidad con comandos antiguos
        test-contacto)
            print_warning "Comando obsoleto. Use 'test-aux' para tests seguros"
            test_contacto_manual "auxiliar" "$2"
            ;;
        *)
            print_error "Comando no reconocido: $1"
            echo ""
            echo -e "Use: ${CYAN}$0 help${NC} para ver todos los comandos disponibles"
            echo ""
            echo -e "${YELLOW}Comandos mas comunes V2.1:${NC}"
            echo -e "  $0 start              # Iniciar simulador"
            echo -e "  $0 status             # Ver estado"
            echo -e "  $0 logs               # Ver actividad"
            echo -e "  $0 precio 60          # Cambiar precio"
            echo -e "  $0 test-aux           # Test seguro"
            echo -e "  $0 pagos              # Ver pagos"
            exit 1
            ;;
    esac
}

# Ejecutar funcion principal con todos los argumentos
main "$@"