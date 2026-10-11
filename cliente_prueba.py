# -*- coding: utf-8 -*-
"""
cliente_prueba.py  -  Prueba tu motor de IA desde cualquier PC.

Sirve para verificar que el motor de la nube responde bien.
Tambien es un ejemplo de como conectarte desde tus propios programas.

USO:
   python cliente_prueba.py
   python cliente_prueba.py http://IP_DE_TU_NUBE:11435
"""

import sys
import json
import requests

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:11435").rstrip("/")
CLAVE = ""  # si le pusiste clave al motor, escribila aca


def _headers():
    h = {"Content-Type": "application/json"}
    if CLAVE:
        h["Authorization"] = f"Bearer {CLAVE}"
    return h


def probar():
    print("=" * 60)
    print(f"  Probando el motor en: {URL}")
    print("=" * 60)

    # 1) Health
    try:
        r = requests.get(f"{URL}/health", timeout=6)
        print(f"[1] /health -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"[!] No pude conectar al motor: {e}")
        print("    Revisa la IP, el puerto y que el servicio este corriendo.")
        return

    # 2) Estado
    try:
        r = requests.get(f"{URL}/estado", timeout=10)
        print(f"[2] /estado -> {json.dumps(r.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"[2] /estado -> error: {e}")

    # 3) Chat simple
    try:
        r = requests.post(f"{URL}/api/chat", headers=_headers(),
                          json={"texto": "Decime hola en una linea."}, timeout=120)
        print(f"[3] chat simple -> {r.json().get('respuesta')}")
    except Exception as e:
        print(f"[3] chat simple -> error: {e}")

    # 4) Pensar con herramientas
    try:
        r = requests.post(f"{URL}/api/pensar", headers=_headers(),
                          json={"texto": "Que hora es y cuanto es 25*4?"}, timeout=180)
        d = r.json()
        print(f"[4] pensar (con herramientas) -> {d.get('respuesta')}")
        print(f"    herramientas usadas: {d.get('herramientas_usadas')}")
    except Exception as e:
        print(f"[4] pensar -> error: {e}")

    # 5) API compatible con OpenAI
    try:
        r = requests.post(f"{URL}/v1/chat/completions", headers=_headers(),
                          json={"model": "jarvis-fer",
                                "messages": [{"role": "user", "content": "Contame un chiste corto."}]},
                          timeout=120)
        texto = r.json()["choices"][0]["message"]["content"]
        print(f"[5] API OpenAI -> {texto}")
    except Exception as e:
        print(f"[5] API OpenAI -> error: {e}")

    print("=" * 60)
    print("  Si viste respuestas en [3], [4] y [5], tu motor FUNCIONA.")
    print("=" * 60)


if __name__ == "__main__":
    probar()
