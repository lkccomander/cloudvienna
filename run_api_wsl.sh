#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv-linux/bin/python" ]; then
  echo "[ERROR] No existe .venv-linux. Ejecuta primero: ./setup_wsl.sh"
  exit 1
fi

.venv-linux/bin/python -m backend.run
