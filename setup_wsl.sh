#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 no esta disponible en este entorno."
  exit 1
fi

if [ ! -d ".venv-linux" ]; then
  echo "[INFO] Creando entorno virtual Linux en .venv-linux ..."
  python3 -m venv .venv-linux
fi

echo "[INFO] Instalando dependencias Linux ..."
.venv-linux/bin/python -m pip install -r requirements-linux.txt

echo "[OK] Entorno WSL listo."
echo "Usa:"
echo "  ./run_tests_wsl.sh"
echo "  ./run_api_wsl.sh"
echo "  ./run_gui_wsl.sh"
