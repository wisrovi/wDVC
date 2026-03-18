#!/bin/bash

set -euo pipefail

# Function for logging
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $level - $message" >&2
}

# Script to pull DVC data for a specified folder
# Usage: ./download_complete_folder.sh <folder_name>

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists dvc; then
    log "ERROR" "dvc is not installed or not in the PATH."
    exit 1
fi

if [ -z "${1-}" ]; then
    log "ERROR" "No folder name was provided."
    log "INFO" "Usage: $0 <folder_name>"
    exit 1
fi

folder_name="$1"
dvc_file="${folder_name}.dvc"

# Check if the .dvc file exists
if [ ! -f "$dvc_file" ]; then
    log "ERROR" "The DVC file '$dvc_file' does not exist in the current directory."
    log "INFO" "Note: This script assumes the .dvc file is named <folder_name>.dvc and is in the current directory."
    log "INFO" "For more robust DVC file discovery, consider using 'dvc list' or 'dvc root' to locate the correct .dvc file."
    exit 1
fi

log "INFO" "Executing 'dvc pull $dvc_file'..."
dvc pull "$dvc_file"

log "INFO" "Pull complete for '$folder_name'."
