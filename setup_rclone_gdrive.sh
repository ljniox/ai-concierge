#!/bin/bash

# Script de configuration rclone pour Google Drive
echo "Configuration de rclone pour Google Drive"

# Installation de rclone si nécessaire
if ! command -v rclone &> /dev/null; then
    echo "Installation de rclone..."
    # Pour macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install rclone
    # Pour Linux/Ubuntu
    else
        curl https://rclone.org/install.sh | sudo bash
    fi
fi

# Configuration interactive de rclone
echo "Lancement de la configuration rclone..."
rclone config

echo "Configuration terminée!"
echo ""
echo "Pour utiliser rclone:"
echo "1. Lister les fichiers: rclone ls gdrive:"
echo "2. Synchroniser un dossier: rclone sync /path/to/local gdrive:backup"
echo "3. Copier des fichiers: rclone copy /path/to/file gdrive:backup/"