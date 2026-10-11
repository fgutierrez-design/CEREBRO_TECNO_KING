# -*- coding: utf-8 -*-
"""
motor_core.py  -  El CEREBRO de TU motor de IA.

Este archivo le da al motor la capacidad de "pensar y actuar":
  1. Recibe lo que le pedis.
  2. Decide si necesita usar una herramienta (buscar en web, escribir
     un archivo, ejecutar codigo, recordar algo...).
  3. La ejecuta, ve el resultado, y sigue pensando.
  4. Repite hasta tener la respuesta final.

Es el mismo concepto que usan los agentes grandes (como yo): un
bucle de "pensar -> actuar -> observar".

Funciona con Ollama (local o en tu nube con GPU).
"""

import os
import json
import time
from pathlib import Path
import requests

import herramientas

_DIR = Path(__file__).resolve().parent
_CONFIG = _DIR / "config_motor.json"

# ------------------------------------------------------------------
#  CONFIGURACION
# ------------------------------------------------------------------
_DEFAULT = {
    "url_ollama": "http://127.0.0.1:11434",
    "modelo": "jarvis-fer",
    "clave": "",
    "temperatura": 0.6,
    "max_tokens": 1024,
    "max_pasos": 6,            # cuantas veces puede usar herramientas por consulta
    "usar_herramientas": True,
    "timeout_segundos": 180,
    "personalidad": (
        "Sos JARVIS FER, el motor de IA propio de TECNO G (La Punta, San Luis, Argentina). "
        "Hablás en español argentino: claro, corto, directo y canchero. "
        "Sos técnico en PC, celulares y redes. Das la solución y ofrecés el servicio. "
        "Si no sabés algo, lo decís con honestidad en vez de inventar. "
        "Cuando te pidan un programa, devolvés el código listo para copiar y pegar."
    ),
}


def cargar_config():
    cfg = dict(_DEFAULT)
    try:
        if _CONFIG.exists():
            cfg.update(json.loads(_CONFIG.read_text(encoding="utf-8")))
    except Exception:
        pass
    # Variables de entorno tienen prioridad
    if os.environ.get("OLLAMA_URL"):
        cfg["url_ollama"] = os.environ["OLLAMA_URL"]
    if os.environ.get("JARVIS_MOTOR"):
        cfg["modelo"] = os.environ["JARVIS_MOTOR"]
    if os.environ.get("OLLAMA_API_KEY"):
        cfg["clave"] = os.environ["OLLAMA_API_KEY"]
    cfg["url_ollama"] = cfg["url_ollama"].rstrip("/")
    return cfg


def _headers(cfg):
    h = {"Content-Type": "application/json"}
    if cfg.get("clave"):
        h["Authorization"] = f"Bearer {cfg['clave']}"
    return h


def motor_vivo(cfg=None, timeout=4):
    cfg = cfg or cargar_config()
    try:
        r = requests.get(f"{cfg['url_ollama']}/api/tags", headers=_headers(cfg), timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def modelo_listo(cfg=None, timeout=6):
    cfg = cfg or cargar_config()
    try:
        r = requests.get(f"{cfg['url_ollama']}/api/tags", headers=_headers(cfg), timeout=timeout)
        if r.status_code != 200:
            return False
        modelos = [m.get("name", "") for m in r.json().get("models", [])]
        return any(cfg["modelo"] in m for m in modelos)
    except Exception:
        return False


# ------------------------------------------------------------------
#  LLAMADA AL MODELO
# ------------------------------------------------------------------
def _llamar_modelo(cfg, mensajes, herramientas_def=None):
    """Hace UNA llamada al modelo. Devuelve el mensaje del assistant (dict)."""
    payload = {
        "model": cfg["modelo"],
        "messages": mensajes,
        "stream": False,
        "options": {
            "temperature": cfg["temperatura"],
            "num_predict": cfg["max_tokens"],
        },
    }
    if herramientas_def:
        payload["tools"] = herramientas_def
    r = requests.post(
        f"{cfg['url_ollama']}/api/chat",
        headers=_headers(cfg),
        json=payload,
        timeout=cfg["timeout_segundos"],
    )
    r.raise_for_status()
    return r.json().get("message", {})


# ------------------------------------------------------------------
#  BUCLE AGENTE (pensar -> actuar -> observar)
# ------------------------------------------------------------------
def pensar(mensaje, historial=None, cfg=None, usar_herramientas=None):
    """Resuelve una consulta usando el bucle agente.

    mensaje:   texto del usuario
    historial: lista de mensajes previos [{"role","content"}, ...]
    Devuelve un dict: {"respuesta": str, "pasos": [...], "herramientas_usadas": [...]}
    """
    cfg = cfg or cargar_config()
    if usar_herramientas is None:
        usar_herramientas = cfg.get("usar_herramientas", True)

    mensajes = [{"role": "system", "content": cfg["personalidad"]}]
    if historial:
        mensajes.extend(historial[-12:])  # memoria corta (ultimos 12 mensajes)
    mensajes.append({"role": "user", "content": mensaje})

    defs = herramientas.definiciones_para_modelo() if usar_herramientas else None
    pasos = []
    usadas = []

    for _ in range(int(cfg.get("max_pasos", 6))):
        try:
            resp = _llamar_modelo(cfg, mensajes, defs)
        except Exception as e:
            return {"respuesta": f"Error del motor: {e}", "pasos": pasos, "herramientas_usadas": usadas}

        tool_calls = resp.get("tool_calls") or []
        contenido = resp.get("content", "") or ""

        # Sin herramientas -> respuesta final
        if not tool_calls:
            return {"respuesta": contenido.strip() or "(sin respuesta)", "pasos": pasos,
                    "herramientas_usadas": usadas}

        # Guardamos el mensaje del assistant (con los tool_calls) para el contexto
        mensajes.append({"role": "assistant", "content": contenido, "tool_calls": tool_calls})

        # Ejecutamos cada herramienta pedida
        for tc in tool_calls:
            fn = tc.get("function", {})
            nombre = fn.get("name", "")
            args = fn.get("arguments", {})
            resultado = herramientas.ejecutar(nombre, args)
            usadas.append(nombre)
            pasos.append({"herramienta": nombre, "argumentos": args, "resultado": resultado[:500]})
            mensajes.append({"role": "tool", "content": resultado, "name": nombre})

    # Si se quedo sin pasos, pedimos un cierre
    mensajes.append({"role": "user", "content": "Cerra y dame la respuesta final en texto."})
    try:
        resp = _llamar_modelo(cfg, mensajes, None)
        return {"respuesta": (resp.get("content") or "").strip(), "pasos": pasos,
                "herramientas_usadas": usadas}
    except Exception as e:
        return {"respuesta": f"Error del motor: {e}", "pasos": pasos, "herramientas_usadas": usadas}


def chat_simple(mensaje, historial=None, cfg=None):
    """Respuesta directa SIN herramientas (mas rapido). Devuelve texto."""
    cfg = cfg or cargar_config()
    mensajes = [{"role": "system", "content": cfg["personalidad"]}]
    if historial:
        mensajes.extend(historial[-12:])
    mensajes.append({"role": "user", "content": mensaje})
    try:
        resp = _llamar_modelo(cfg, mensajes, None)
        return (resp.get("content") or "").strip()
    except Exception as e:
        return f"Error del motor: {e}"


def estado():
    cfg = cargar_config()
    vivo = motor_vivo(cfg)
    return {
        "url": cfg["url_ollama"],
        "modelo": cfg["modelo"],
        "con_clave": bool(cfg.get("clave")),
        "herramientas": cfg.get("usar_herramientas", True),
        "motor_respondiendo": vivo,
        "modelo_listo": modelo_listo(cfg) if vivo else False,
        "modo": "remoto (nube)" if ("127.0.0.1" not in cfg["url_ollama"] and "localhost" not in cfg["url_ollama"]) else "local (PC)",
        "herramientas_disponibles": herramientas.NOMBRES,
    }


if __name__ == "__main__":
    print(json.dumps(estado(), ensure_ascii=False, indent=2))
    if motor_vivo() and modelo_listo():
        print("\n--- Prueba ---")
        print(pensar("Decime que hora es y cuanto es 12*8.")["respuesta"])
