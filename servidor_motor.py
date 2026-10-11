# -*- coding: utf-8 -*-
"""
servidor_motor.py  -  El servidor que expone TU motor de IA.

Levanta una API HTTP para que tu JARVIS (u otro programa) pueda
"pensar" usando el motor que vive en la nube.

Endpoints:
  GET  /                       -> pagina de estado simple
  GET  /health                 -> chequear que esta vivo
  GET  /estado                 -> estado completo del motor
  GET  /v1/models              -> lista de modelos (formato OpenAI)
  POST /v1/chat/completions    -> API COMPATIBLE CON OPENAI (con streaming)
  POST /api/pensar             -> API nativa con HERRAMIENTAS (agente)
  POST /api/chat               -> chat simple y rapido

Puerto por defecto: 11435 (configurable con JARVIS_MOTOR_PUERTO).
"""

import os
import json
import time
from pathlib import Path

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

import motor_core

app = Flask(__name__)
CORS(app)

PUERTO = int(os.environ.get("JARVIS_MOTOR_PUERTO", "11435"))
CLAVE = os.environ.get("JARVIS_MOTOR_CLAVE", "")  # si se define, exige Bearer


def _autorizado():
    if not CLAVE:
        return True
    cabecera = request.headers.get("Authorization", "")
    return cabecera == f"Bearer {CLAVE}"


def _no_autorizado():
    return jsonify({"error": {"message": "Clave incorrecta o faltante.", "type": "auth_error"}}), 401


# ------------------------------------------------------------------
#  ESTADO
# ------------------------------------------------------------------
@app.route("/", methods=["GET"])
def raiz():
    e = motor_core.estado()
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Motor JARVIS - TECNO G</title>
<style>body{{font-family:system-ui;background:#0b1020;color:#e6edf3;padding:40px}}
h1{{color:#5eead4}} .ok{{color:#4ade80}} .no{{color:#f87171}}
code{{background:#1e293b;padding:2px 6px;border-radius:4px}}</style></head><body>
<h1>Motor de IA JARVIS - TECNO G</h1>
<p>Estado: <b class="{'ok' if e['motor_respondiendo'] else 'no'}">
{'FUNCIONANDO' if e['motor_respondiendo'] else 'DETENIDO'}</b></p>
<p>Modelo: <code>{e['modelo']}</code> &nbsp; Modo: <b>{e['modo']}</b></p>
<p>Herramientas: {', '.join(e['herramientas_disponibles'])}</p>
<hr><p>API compatible con OpenAI en <code>/v1/chat/completions</code></p>
</body></html>"""


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "servicio": "motor-jarvis", "hora": time.time()})


@app.route("/estado", methods=["GET"])
def estado():
    return jsonify(motor_core.estado())


@app.route("/v1/models", methods=["GET"])
def modelos():
    if not _autorizado():
        return _no_autorizado()
    cfg = motor_core.cargar_config()
    return jsonify({
        "object": "list",
        "data": [{"id": cfg["modelo"], "object": "model", "owned_by": "tecno-g"}],
    })


# ------------------------------------------------------------------
#  API COMPATIBLE CON OPENAI
# ------------------------------------------------------------------
@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    if not _autorizado():
        return _no_autorizado()
    data = request.get_json(force=True, silent=True) or {}
    mensajes = data.get("messages", [])
    stream = bool(data.get("stream", False))

    # Separamos el system y tomamos el ultimo mensaje del usuario
    historial = [m for m in mensajes if m.get("role") in ("user", "assistant")]
    ultimo = next((m["content"] for m in reversed(mensajes) if m.get("role") == "user"), "")

    cfg = motor_core.cargar_config()
    if "temperature" in data:
        cfg["temperatura"] = data["temperature"]
    if "max_tokens" in data:
        cfg["max_tokens"] = data["max_tokens"]

    if stream:
        def generar():
            texto = motor_core.chat_simple(ultimo, historial[:-1], cfg)
            for palabra in texto.split(" "):
                chunk = {
                    "id": "chatcmpl-jarvis", "object": "chat.completion.chunk",
                    "created": int(time.time()), "model": cfg["modelo"],
                    "choices": [{"index": 0, "delta": {"content": palabra + " "}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            fin = {"id": "chatcmpl-jarvis", "object": "chat.completion.chunk",
                   "created": int(time.time()), "model": cfg["modelo"],
                   "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {json.dumps(fin, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return Response(stream_with_context(generar()), mimetype="text/event-stream")

    texto = motor_core.chat_simple(ultimo, historial[:-1], cfg)
    return jsonify({
        "id": "chatcmpl-jarvis", "object": "chat.completion", "created": int(time.time()),
        "model": cfg["modelo"],
        "choices": [{"index": 0, "message": {"role": "assistant", "content": texto},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    })


# ------------------------------------------------------------------
#  API NATIVA (con herramientas)
# ------------------------------------------------------------------
@app.route("/api/pensar", methods=["POST"])
def api_pensar():
    if not _autorizado():
        return _no_autorizado()
    data = request.get_json(force=True, silent=True) or {}
    texto = data.get("texto") or data.get("mensaje") or data.get("query") or ""
    if not texto.strip():
        return jsonify({"error": "Falta el texto."}), 400
    historial = data.get("historial", [])
    usar = data.get("usar_herramientas", True)
    resultado = motor_core.pensar(texto, historial, usar_herramientas=usar)
    return jsonify(resultado)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not _autorizado():
        return _no_autorizado()
    data = request.get_json(force=True, silent=True) or {}
    texto = data.get("texto") or data.get("mensaje") or data.get("query") or ""
    if not texto.strip():
        return jsonify({"error": "Falta el texto."}), 400
    respuesta = motor_core.chat_simple(texto, data.get("historial", []))
    return jsonify({"respuesta": respuesta})


if __name__ == "__main__":
    e = motor_core.estado()
    print("=" * 60)
    print("  MOTOR DE IA JARVIS - TECNO G")
    print("=" * 60)
    print(f"  Puerto:  {PUERTO}")
    print(f"  Modelo:  {e['modelo']}  ({e['modo']})")
    print(f"  Motor:   {'OK' if e['motor_respondiendo'] else 'NO responde (revisa Ollama)'}")
    print(f"  Clave:   {'SI' if CLAVE else 'no (abierto)'}")
    print("-" * 60)
    print(f"  API OpenAI:  http://0.0.0.0:{PUERTO}/v1/chat/completions")
    print(f"  API nativa:  http://0.0.0.0:{PUERTO}/api/pensar")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PUERTO, threaded=True)
