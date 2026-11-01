#!/usr/bin/env bash
# Sert le site généré sur le réseau local (port 8080).
set -euo pipefail
cd "$(dirname "$0")/../dist"
HOST_IP=$(ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -n1)
echo "→ http://${HOST_IP:-localhost}:8080"
exec python3 -m http.server 8080 --bind 0.0.0.0
