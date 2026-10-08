#!/usr/bin/env bash
set -euo pipefail
p2_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$p2_root"
p2_python="$p2_root/.venv-vision/bin/python"
if [[ ! -x "$p2_python" || ! -x "$p2_root/.venv/bin/python" ]]; then
    echo 'Faltan entornos. Ejecuta ./instalar.sh con Python 3.12.' >&2
    exit 2
fi
case "${1:-tutor}" in
    cara|ojos|manos|expresion)
        p2_detector="$1"; shift
        exec "$p2_python" "$p2_root/scripts/probar_detector.py" "$p2_detector" "$@"
        ;;
    tutor) if [[ $# -gt 0 ]]; then shift; fi ;;
esac
exec "$p2_python" -m tutor "$@"
