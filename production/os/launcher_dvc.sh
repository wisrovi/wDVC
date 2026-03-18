#!/bin/bash
# Launcher for DVC Worker Stack
# Author: William Rodríguez - wisrovi

COMPOSE_DIR="/home/wisrovi/dvc"

echo "[$(date)] Validando estado del Stack DVC..."

if cd "$COMPOSE_DIR"; then
    /usr/bin/docker compose up -d --pull always
    echo "[$(date)] Stack validado y en ejecución."
else
    echo "[$(date)] ERROR: No se pudo acceder a $COMPOSE_DIR"
    exit 1
fi