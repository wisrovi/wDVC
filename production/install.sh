#!/bin/bash
# Installer for DVC Worker Service
# Author: William Rodríguez - wisrovi

TARGET_DIR="/home/wisrovi/dvc"
INSTANCE_NAME="main"

# Rutas de origen según tu estructura 'tree'
SRC_COMPOSE="docker/docker-compose.worker.production.yaml"
SRC_SERVICE="os/datasetIA_worker@.service"
SRC_TIMER="os/datasetIA_worker@.timer"
SRC_LAUNCHER="os/launcher_dvc.sh"

echo "-------------------------------------------------------"
echo "  Instalador de DVC Worker - William Rodríguez"
echo "-------------------------------------------------------"

# --- 1. PREPARACIÓN ---
echo "[+] Creando directorio de trabajo..."
sudo mkdir -p "$TARGET_DIR"

# --- 2. DESPLIEGUE DE ARCHIVOS ---
echo "[+] Copiando Docker Compose..."
sudo cp "$SRC_COMPOSE" "$TARGET_DIR/docker-compose.yml"

echo "[+] Copiando Launcher..."
sudo cp "$SRC_LAUNCHER" "$TARGET_DIR/"
sudo chmod +x "$TARGET_DIR/launcher_dvc.sh"

echo "[+] Instalando archivos de Systemd..."
sudo cp "$SRC_SERVICE" "/etc/systemd/system/"
sudo cp "$SRC_TIMER" "/etc/systemd/system/"

# Ajuste de permisos para el usuario wisrovi
sudo chown -R wisrovi:wisrovi "$TARGET_DIR"

# --- 3. ACTIVACIÓN ---
echo "[+] Recargando Systemd y activando Timer..."
sudo systemctl daemon-reload

# Habilitamos e iniciamos el TIMER (no el service directamente)
# Esto garantiza que se ejecute cada 10 min.
sudo systemctl enable --now "datasetIA_worker@${INSTANCE_NAME}.timer"

echo "-------------------------------------------------------"
echo "¡Instalación completada con éxito!"
echo "Estado del timer:"
sudo systemctl status "datasetIA_worker@${INSTANCE_NAME}.timer" --no-pager
echo "-------------------------------------------------------"