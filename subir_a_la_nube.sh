#!/usr/bin/env bash
# ============================================================
#  subir_a_la_nube.sh  -  Sube el motor a tu servidor (Linux/Mac)
#
#  USO:
#    bash subir_a_la_nube.sh usuario@IP_DE_TU_NUBE [carpeta_destino]
#
#  Ejemplo:
#    bash subir_a_la_nube.sh fer@203.0.113.10 /home/fer/motor
#
#  Requiere: rsync (o scp) y acceso SSH a tu nube.
# ============================================================
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DESTINO="${1:-}"
CARPETA="${2:-~/MOTOR_COMPLETO}"

if [ -z "$DESTINO" ]; then
  echo "Uso: bash subir_a_la_nube.sh usuario@IP_DE_TU_NUBE [carpeta_destino]"
  echo "Ej : bash subir_a_la_nube.sh fer@203.0.113.10 /home/fer/motor"
  exit 1
fi

echo "============================================================"
echo "  Subiendo el motor a: $DESTINO:$CARPETA"
echo "============================================================"

# Crea la carpeta destino
ssh "$DESTINO" "mkdir -p $CARPETA"

if command -v rsync >/dev/null 2>&1; then
  echo "[..] Usando rsync..."
  rsync -avz --progress \
    --exclude ".venv" --exclude "__pycache__" --exclude "trabajo" \
    --exclude "*.log" --exclude "memoria_motor.json" \
    "$DIR/" "$DESTINO:$CARPETA/"
else
  echo "[..] rsync no disponible, usando scp..."
  scp -r "$DIR"/* "$DESTINO:$CARPETA/"
fi

echo ""
echo "[OK] Codigo subido a tu nube."
echo ""
echo "AHORA entra por SSH y corre el instalador:"
echo "   ssh $DESTINO"
echo "   cd $CARPETA"
echo "   bash instalar_motor.sh"
