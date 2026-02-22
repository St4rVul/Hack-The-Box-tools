#!/bin/bash

# Configuración
VPN_DIR="/home/star/HTB/VPN/" # Cambiar a su directorio donde tenga las vpns 
# Colores para que se vea bien
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
GREEN='\033[1;32m'
NC='\033[0m' 
# 1. Verificar si OpenVPN está instalado
if ! command -v openvpn &> /dev/null; then
    echo -e "${RED}Error: OpenVPN no está instalado.${NC}"
    exit 1
fi

# 2. Cambiar al directorio y listar archivos .ovpn en un array
cd "$VPN_DIR" || { echo -e "${RED}Error: Directorio VPN no encontrado${NC}"; exit 1; }
shopt -s nullglob # Evita errores si no hay archivos .ovpn
files=(*.ovpn)

if [ ${#files[@]} -eq 0 ]; then
    echo -e "${RED}No se encontraron archivos .ovpn en $VPN_DIR${NC}"
    exit 1
fi

# 3. Limpiar conexiones previas
sudo pkill -f openvpn

# 4. Mostrar menú dinámico
echo -e "\n${CYAN}--- VPNs de HackTheBox Detectadas ---${NC}"
for i in "${!files[@]}"; do
    printf "%2d) %s\n" "$((i+1))" "${files[$i]}"
done

echo -e "\n${YELLOW}Selecciona una opción (1-${#files[@]}) o presiona Enter para la primera:${NC}"
read -r choice

# 5. Lógica de selección
if [[ -z "$choice" ]]; then
    SELECTED="${files[0]}" # Default es la primera de la lista
elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#files[@]}" ]; then
    SELECTED="${files[$((choice-1))]}"
else
    echo -e "${RED}Opción inválida.${NC}"
    exit 1
fi



# 6. Conectar
echo -e "\n${GREEN}Conectando a: $SELECTED...${NC}"
sudo openvpn --config "$SELECTED" > /dev/null 2>&1 &

echo -n "Esperando a que la interfaz tun0 levante..."
for i in {1..10}; do
    if ip addr show tun0 &> /dev/null; then
              VPN_IP=$(ip addr show tun0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        
        echo -e "\n${GREEN}[✔] ¡Conectado!${NC}"
        echo -e "${CYAN}Tu IP de HTB es: ${NC}${YELLOW}$VPN_IP${NC}"   
        break
    fi
    echo -n "."
    sleep 1
done

if ! ip addr show tun0 &> /dev/null; then
    echo -e "\n${RED}[✘] Error: La interfaz tun0 no levantó a tiempo.${NC}"
fi
