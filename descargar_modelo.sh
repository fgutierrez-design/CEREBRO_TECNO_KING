#!/usr/bin/env bash
# ============================================================
#  descargar_modelo.sh  -  Baja un modelo base y (re)crea tu motor
#
#  USO:
#    bash descargar_modelo.sh qwen2.5-coder:7b
#    bash descargar_modelo.sh qwen2.5:14b
# ============================================================
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

MODELO="${1:-qwen2.5:7b}"

echo "============================================================"
echo "  Bajando modelo base: $MODELO"
echo "============================================================"

if ! command -v ollama >/dev/null 2>&1; then
  echo "[!] Ollama no esta instalado. Corre primero: bash instalar_motor.sh"
  exit 1
fi

ollama pull "$MODELO"

echo ""
echo "[..] Recreando tu motor 'jarvis-fer' con el nuevo base..."
cp Modelfile Modelfile.bak
sed -i "s|^FROM .*|FROM $MODELO|" Modelfile
ollama create jarvis-fer -f Modelfile
mv Modelfile.bak Modelfile

echo ""
echo "[OK] Listo. Tu motor 'jarvis-fer' ahora usa '$MODELO'."
echo "     Probalo con:  ollama run jarvis-fer"
