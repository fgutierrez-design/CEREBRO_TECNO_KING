#!/usr/bin/env bash
# ============================================================
#  instalar_motor.sh  -  INSTALADOR TODO-EN-UNO del motor JARVIS
#
#  Deja tu nube (servidor Linux con GPU) lista para pensar:
#    - Instala Ollama
#    - Baja el modelo base
#    - Crea TU motor "jarvis-fer"
#    - Instala el servidor de la API y el de conocimiento
#    - Los deja arrancando SOLOS (servicios del sistema)
#
#  USO:   bash instalar_motor.sh
#  (Opcional) elegir el modelo base:
#         MODELO_BASE=qwen2.5-coder:7b bash instalar_motor.sh
# ============================================================
set -e

VERDE="\033[1;32m"; AMAR="\033[1;33m"; ROJO="\033[1;31m"; NC="\033[0m"
ok(){ echo -e "${VERDE}[OK]${NC} $1"; }
info(){ echo -e "${AMAR}[..]${NC} $1"; }
err(){ echo -e "${ROJO}[!]${NC} $1"; }

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "   MOTOR DE IA JARVIS - TECNO G   |   Instalador para la nube"
echo "============================================================"
echo "Carpeta: $DIR"
echo ""

# --- 0) Root / sudo ---
SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

# --- 1) Paquetes base ---
info "Paso 1/7: instalando paquetes base (python, curl, git)..."
if command -v apt-get >/dev/null 2>&1; then
  $SUDO apt-get update -y >/dev/null 2>&1 || true
  $SUDO apt-get install -y python3 python3-pip python3-venv curl git >/dev/null 2>&1 || true
elif command -v dnf >/dev/null 2>&1; then
  $SUDO dnf install -y python3 python3-pip curl git >/dev/null 2>&1 || true
fi
ok "paquetes base listos"

# --- 2) Ollama ---
info "Paso 2/7: instalando Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  ok "Ollama ya estaba instalado"
fi

# --- 3) Ollama escuchando en la red ---
info "Paso 3/7: configurando Ollama para aceptar conexiones..."
$SUDO mkdir -p /etc/systemd/system/ollama.service.d
$SUDO tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_KEEP_ALIVE=30m"
EOF
$SUDO systemctl daemon-reload
$SUDO systemctl enable ollama >/dev/null 2>&1 || true
$SUDO systemctl restart ollama || true
sleep 4
ok "Ollama configurado"

# --- 4) Modelo base ---
MODELO_BASE="${MODELO_BASE:-qwen2.5:7b}"
info "Paso 4/7: bajando el modelo base '$MODELO_BASE' (puede tardar bastante)..."
ollama pull "$MODELO_BASE"
ok "modelo base descargado"

# --- 5) Crear TU motor ---
info "Paso 5/7: creando tu motor 'jarvis-fer'..."
if [ -f "Modelfile" ]; then
  cp Modelfile Modelfile.bak
  sed -i "s|^FROM .*|FROM $MODELO_BASE|" Modelfile
  ollama create jarvis-fer -f Modelfile
  mv Modelfile.bak Modelfile
  ok "motor 'jarvis-fer' creado"
else
  err "No encontre Modelfile. Copialo y volve a correr el script."
fi

# --- 6) Entorno Python + dependencias ---
info "Paso 6/7: preparando el servidor de la API..."
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
./.venv/bin/pip install --upgrade pip >/dev/null 2>&1 || true
./.venv/bin/pip install -r requirements.txt >/dev/null 2>&1 || true
ok "dependencias Python instaladas"

# --- 7) Servicios del sistema (arranque automatico) ---
info "Paso 7/7: instalando servicios (arranque automatico)..."
USUARIO_ACTUAL="$(whoami)"

# Servicio del motor (API)
$SUDO tee /etc/systemd/system/jarvis-motor.service >/dev/null <<EOF
[Unit]
Description=Motor de IA JARVIS (API) - TECNO G
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$USUARIO_ACTUAL
WorkingDirectory=$DIR
Environment="JARVIS_MOTOR_PUERTO=11435"
ExecStart=$DIR/.venv/bin/python $DIR/servidor_motor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Servicio de conocimiento (si existe el archivo)
if [ -f "servidor_conocimiento.py" ]; then
  $SUDO tee /etc/systemd/system/jarvis-conocimiento.service >/dev/null <<EOF
[Unit]
Description=Conocimiento JARVIS (sync) - TECNO G
After=network.target

[Service]
Type=simple
User=$USUARIO_ACTUAL
WorkingDirectory=$DIR
Environment="JARVIS_NUBE_PUERTO=8770"
ExecStart=$DIR/.venv/bin/python $DIR/servidor_conocimiento.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

$SUDO systemctl daemon-reload
$SUDO systemctl enable jarvis-motor >/dev/null 2>&1 || true
$SUDO systemctl restart jarvis-motor || true
if [ -f "servidor_conocimiento.py" ]; then
  $SUDO systemctl enable jarvis-conocimiento >/dev/null 2>&1 || true
  $SUDO systemctl restart jarvis-conocimiento || true
fi
sleep 3
ok "servicios instalados"

# --- Prueba final ---
echo ""
info "Probando el motor..."
sleep 2
curl -s http://127.0.0.1:11435/health || echo "(el servicio puede tardar unos segundos en levantar)"
echo ""
ollama run jarvis-fer "Decime en una linea quien sos y para que servis." || true

echo ""
echo "============================================================"
echo -e "${VERDE} LISTO. Tu motor de IA corre en la nube.${NC}"
echo ""
echo "  API del motor:   http://IP_DE_TU_NUBE:11435"
echo "  Ollama directo:  http://IP_DE_TU_NUBE:11434"
echo ""
echo "  SEGURIDAD (MUY IMPORTANTE):"
echo "  1) Pone una clave:  export JARVIS_MOTOR_CLAVE=tu_clave_secreta"
echo "     y reinicia:      sudo systemctl restart jarvis-motor"
echo "  2) O usa un TUNEL SSH desde tu PC (mas seguro):"
echo "       ssh -L 11435:localhost:11435 -L 8770:localhost:8770 usuario@IP_DE_TU_NUBE"
echo "  3) En el firewall de tu proveedor, abri los puertos SOLO a tu IP."
echo "============================================================"
