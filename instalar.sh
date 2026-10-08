#!/usr/bin/env bash
# Dos entornos mantienen separadas las distribuciones incompatibles que aportan cv2.
set -euo pipefail
p2_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$p2_root"
p2_bootstrap_python="${P2_PYTHON:-python3}"
"$p2_bootstrap_python" -c 'import sys; assert sys.version_info[:2] == (3,12), "Esta instalación fijada se ha comprobado con Python 3.12"'
for p2_env in .venv-vision .venv; do
    if [[ ! -x "$p2_root/$p2_env/bin/python" ]]; then
        "$p2_bootstrap_python" -m venv "$p2_root/$p2_env"
    fi
done
"$p2_root/.venv-vision/bin/python" -m pip install -r requirements-vision.lock.txt
"$p2_root/.venv/bin/python" -m pip install -r requirements-expression.lock.txt
"$p2_root/.venv-vision/bin/python" -m pip check
"$p2_root/.venv/bin/python" -m pip check
"$p2_root/.venv-vision/bin/python" scripts/comprobar_instalacion.py
"$p2_root/.venv/bin/python" scripts/preparar_expresion.py
"$p2_root/.venv-vision/bin/python" -m unittest discover -s tests -v
printf '\nInstalación comprobada. Ejecuta ./ejecutar.sh cara para empezar con tu cámara.\n'
