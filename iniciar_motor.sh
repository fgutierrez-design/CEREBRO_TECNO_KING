#!/usr/bin/env bash
# ============================================================
#  iniciar_motor.sh  -  Arranca el motor a mano (sin servicios)
#  Util para probar. Para uso permanente usa los servicios
#  que instala instalar_motor.sh (arrancan solos).
# ============================================================
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

export JARVIS_MOTOR_PUERTO="${JARVIS_MOTOR_PUERTO:-11435}"

echo "Arrancando el motor JARVIS en el puerto $JARVIS_MOTOR_PUERTO..."
echo "(Ctrl+C para detener)"

# Asegura que Ollama este corriendo
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "[..] Arrancando Ollama..."
  ollama serve >/dev/null 2>&1 &
  sleep 3
fi

# Servidor de conocimiento en segundo plano (si existe)
if [ -f "servidor_conocimiento.py" ]; then
  echo "[..] Arrancando servidor de conocimiento (8770)..."
  python3 servidor_conocimiento.py >/dev/null 2>&1 &
fi

# Motor (API) en primer plano
python3 servidor_motor.py
