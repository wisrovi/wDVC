#!/bin/bash

set -euo pipefail # Exit on error, undefined variable, or pipe failure

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for dependencies
if ! command_exists python; then
    echo "Error: python is not installed or not in the PATH." >&2
    exit 1
fi

if ! command_exists dvc; then
    echo "Error: dvc is not installed or not in the PATH." >&2
    exit 1
fi

# Check if an argument is provided
if [ -z "${1-}" ]; then
    # If no argument is provided, print an error message and usage instructions
    echo "Error: No parameter was provided." >&2
    echo "Usage: $0 <folder_path>" >&2
    exit 1  # Exit the script with a non-zero status to indicate failure
fi

# Capture the first argument (folder path)
folder_path="$1"

# Print the received parameter
echo "The provided folder is: $folder_path"

# Check if the folder exists
if [ ! -d "$folder_path" ]; then
    # If the folder does not exist, print an error message and exit
    echo "Error: The folder '$folder_path' does not exist." >&2
    exit 1  # Exit the script with a non-zero status to indicate failure
fi
echo "The folder '$folder_path' exists."

rm -rf /app/.dvc/cache 
rm -rf /app/.dvc/tmp

# Get the directory where the script is located
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
INVENTORY_SCRIPT="$SCRIPT_DIR/files_inventory.py"
OUTPUT_CSV="$folder_path.csv"

# Check if inventory script exists
if [ ! -f "$INVENTORY_SCRIPT" ]; then
    echo "Error: Inventory script not found at $INVENTORY_SCRIPT" >&2
    exit 1
fi

# this script create the file: file_list.csv
echo "Generating file inventory..."
if ! python "$INVENTORY_SCRIPT" "$folder_path"; then
    echo "Error: Failed to generate file inventory." >&2
    exit 1
fi

# Check if the CSV was created
if [ ! -f "$OUTPUT_CSV" ]; then
    echo "Error: The inventory CSV file '$OUTPUT_CSV' was not created." >&2
    exit 1
fi

echo "Copying inventory file..."
cp "$OUTPUT_CSV" "$folder_path/"

# up to dvc
echo "Adding folder to DVC..."
dvc add "$folder_path"



echo "borrando lock para evitar bloqueos"
rm -rf /app/tmp/lock



echo "Pushing to DVC remote..."
dvc push

echo "Done."
