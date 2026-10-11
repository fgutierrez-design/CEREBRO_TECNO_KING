# -*- coding: utf-8 -*-
"""
servidor_conocimiento.py  -  Servidor de CONOCIMIENTO en la nube.

Aca vive la "memoria" de JARVIS: los archivos JSON con lo que sabe
(sistema, programacion, trading, clima, memoria, mejoras...).
Tu JARVIS del disco externo los baja al iniciar y los sube al cambiar.

Endpoints:
  GET  /salud                     -> estado
  GET  /conocimiento/lista        -> lista de archivos disponibles
  GET  /conocimiento/<nombre>     -> descarga un archivo
  POST /conocimiento/<nombre>     -> sube/actualiza un archivo

Puerto por defecto: 8770 (configurable con JARVIS_NUBE_PUERTO).
Seguridad: define JARVIS_NUBE_CLAVE para exigir clave.
"""

import os
import json
import shutil
from pathlib import Path

from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

_DIR = Path(__file__).resolve().parent
PUERTO = int(os.environ.get("JARVIS_NUBE_PUERTO", "8770"))
CLAVE = os.environ.get("JARVIS_NUBE_CLAVE", "")
CARPETA = Path(os.environ.get("JARVIS_NUBE_DIR", str(_DIR / "conocimiento")))
CARPETA.mkdir(parents=True, exist_ok=True)

# Solo se pueden subir/bajar estos archivos (seguridad)
PERMITIDOS = {
    "sistema.json", "programacion.json", "trading.json", "clima.json",
    "conocimiento_base.json", "memoria.json", "mejoras_instaladas.json",
}


def _autorizado():
    if not CLAVE:
        return True
    return request.headers.get("Authorization", "") == f"Bearer {CLAVE}"


@app.route("/salud", methods=["GET"])
def salud():
    return jsonify({"ok": True, "servicio": "conocimiento-jarvis",
                    "archivos": len(list(CARPETA.glob("*.json"))),
                    "con_clave": bool(CLAVE)})


@app.route("/conocimiento/lista", methods=["GET"])
def lista():
    if not _autorizado():
        return jsonify({"error": "no autorizado"}), 401
    archivos = sorted(p.name for p in CARPETA.glob("*.json"))
    return jsonify({"archivos": archivos})


@app.route("/conocimiento/<nombre>", methods=["GET"])
def bajar(nombre):
    if not _autorizado():
        return jsonify({"error": "no autorizado"}), 401
    if nombre not in PERMITIDOS:
        return jsonify({"error": "archivo no permitido"}), 403
    p = CARPETA / nombre
    if not p.exists():
        return jsonify({"error": "no existe"}), 404
    return send_file(p, mimetype="application/json")


@app.route("/conocimiento/<nombre>", methods=["POST"])
def subir(nombre):
    if not _autorizado():
        return jsonify({"error": "no autorizado"}), 401
    if nombre not in PERMITIDOS:
        return jsonify({"error": "archivo no permitido"}), 403
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "JSON invalido"}), 400
    p = CARPETA / nombre
    if p.exists():
        shutil.copy2(p, str(p) + ".bak")  # respaldo
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify({"ok": True, "guardado": nombre})


if __name__ == "__main__":
    print("=" * 60)
    print("  SERVIDOR DE CONOCIMIENTO JARVIS - TECNO G")
    print("=" * 60)
    print(f"  Puerto:  {PUERTO}")
    print(f"  Carpeta: {CARPETA}")
    print(f"  Clave:   {'SI' if CLAVE else 'no (abierto)'}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PUERTO, threaded=True)
