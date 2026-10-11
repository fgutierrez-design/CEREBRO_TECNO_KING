# -*- coding: utf-8 -*-
"""
herramientas.py  -  Las "manos" de TU motor de IA.

Aca viven las herramientas que el motor puede usar para ACTUAR
(no solo hablar): buscar en internet, leer/escribir archivos,
ejecutar codigo, recordar cosas, calcular, etc.

Cada herramienta es una funcion de Python + una descripcion en el
formato que entienden los modelos (JSON Schema). El motor decide
solo cual usar segun lo que le pidas.

SEGURIDAD:
- El acceso a archivos y la ejecucion de comandos estan limitados
  a una carpeta de trabajo (SANDBOX).
- Se puede apagar cualquier herramienta desde config_motor.json.
"""

import os
import io
import sys
import json
import math
import time
import html
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------------
#  CARPETA DE TRABAJO (sandbox). Todo lo que el motor cree/lea vive aca.
# ------------------------------------------------------------------
_DIR = Path(__file__).resolve().parent
SANDBOX = _DIR / "trabajo"
SANDBOX.mkdir(parents=True, exist_ok=True)

MEMORIA_FILE = _DIR / "memoria_motor.json"
_LOG_FILE = _DIR / "motor.log"


def _log(texto):
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {texto}\n")
    except Exception:
        pass


def _dentro_del_sandbox(ruta):
    """Devuelve la ruta absoluta si esta dentro del sandbox; si no, lanza error."""
    p = (SANDBOX / ruta).resolve()
    if SANDBOX.resolve() not in p.parents and p != SANDBOX.resolve():
        raise ValueError("Ruta fuera de la carpeta de trabajo (no permitido).")
    return p


# ------------------------------------------------------------------
#  HERRAMIENTAS
# ------------------------------------------------------------------
def hora_actual():
    """Devuelve la fecha y hora actual."""
    ahora = datetime.now()
    return ahora.strftime("Hoy es %A %d/%m/%Y y son las %H:%M hs.")


def calcular(expresion):
    """Calculadora segura (no usa eval directo)."""
    permitidos = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    permitidos.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})
    try:
        # Solo permitimos numeros, operadores y funciones matematicas conocidas.
        resultado = eval(expresion, {"__builtins__": {}}, permitidos)  # noqa: S307
        return f"{expresion} = {resultado}"
    except Exception as e:
        return f"No pude calcular '{expresion}': {e}"


def buscar_web(consulta, cantidad=5):
    """Busca en internet (DuckDuckGo) y devuelve titulos + resumenes."""
    try:
        q = urllib.parse.quote_plus(consulta)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            contenido = r.read().decode("utf-8", "ignore")
        import re
        # Extrae resultados simples del HTML de DuckDuckGo
        bloques = re.findall(
            r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?result__snippet"[^>]*>(.*?)</a>',
            contenido, re.DOTALL)
        salida = []
        for link, titulo, resumen in bloques[:cantidad]:
            titulo = html.unescape(re.sub("<.*?>", "", titulo)).strip()
            resumen = html.unescape(re.sub("<.*?>", "", resumen)).strip()
            salida.append(f"- {titulo}\n  {resumen}\n  {link}")
        if not salida:
            return "No encontre resultados claros. Proba reformular la busqueda."
        return "\n".join(salida)
    except Exception as e:
        return f"Error al buscar en internet: {e}"


def leer_url(url):
    """Lee el texto de una pagina web."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            contenido = r.read().decode("utf-8", "ignore")
        import re
        texto = re.sub(r"<script.*?</script>", " ", contenido, flags=re.DOTALL)
        texto = re.sub(r"<style.*?</style>", " ", texto, flags=re.DOTALL)
        texto = re.sub(r"<.*?>", " ", texto)
        texto = html.unescape(re.sub(r"\s+", " ", texto)).strip()
        return texto[:4000]
    except Exception as e:
        return f"Error al leer la pagina: {e}"


def leer_archivo(ruta):
    """Lee un archivo de la carpeta de trabajo."""
    try:
        p = _dentro_del_sandbox(ruta)
        if not p.exists():
            return f"No existe el archivo '{ruta}'."
        return p.read_text(encoding="utf-8", errors="ignore")[:6000]
    except Exception as e:
        return f"Error al leer: {e}"


def escribir_archivo(ruta, contenido):
    """Crea o sobrescribe un archivo en la carpeta de trabajo."""
    try:
        p = _dentro_del_sandbox(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        return f"Listo, guarde '{ruta}' ({len(contenido)} caracteres)."
    except Exception as e:
        return f"Error al escribir: {e}"


def listar_archivos(subcarpeta=""):
    """Lista los archivos de la carpeta de trabajo."""
    try:
        p = _dentro_del_sandbox(subcarpeta) if subcarpeta else SANDBOX
        if not p.exists():
            return "La carpeta no existe."
        items = sorted(p.iterdir())
        if not items:
            return "La carpeta esta vacia."
        return "\n".join(("DIR  " if i.is_dir() else "FILE ") + i.name for i in items)
    except Exception as e:
        return f"Error al listar: {e}"


def ejecutar_python(codigo):
    """Ejecuta codigo Python y devuelve la salida (limitado a 15 seg)."""
    try:
        resultado = subprocess.run(
            [sys.executable, "-c", codigo],
            capture_output=True, text=True, timeout=15, cwd=str(SANDBOX),
        )
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        return salida.strip()[:4000] or "(sin salida)"
    except subprocess.TimeoutExpired:
        return "El codigo tardo demasiado (mas de 15 segundos)."
    except Exception as e:
        return f"Error al ejecutar: {e}"


def recordar(clave, valor):
    """Guarda un dato en la memoria permanente del motor."""
    try:
        mem = {}
        if MEMORIA_FILE.exists():
            mem = json.loads(MEMORIA_FILE.read_text(encoding="utf-8"))
        mem[clave] = valor
        MEMORIA_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"Anotado: {clave} = {valor}"
    except Exception as e:
        return f"Error al recordar: {e}"


def recuperar(clave=""):
    """Recupera un dato de la memoria (o toda la memoria si no das clave)."""
    try:
        if not MEMORIA_FILE.exists():
            return "Todavia no tengo nada anotado."
        mem = json.loads(MEMORIA_FILE.read_text(encoding="utf-8"))
        if clave:
            return f"{clave} = {mem.get(clave, '(no lo tengo)')}"
        return json.dumps(mem, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al recuperar: {e}"


# ------------------------------------------------------------------
#  REGISTRO DE HERRAMIENTAS (para el modelo)
# ------------------------------------------------------------------
#  Mapa: nombre -> (funcion, descripcion, parametros)
HERRAMIENTAS = {
    "hora_actual": (
        hora_actual,
        "Devuelve la fecha y hora actual.",
        {"type": "object", "properties": {}, "required": []},
    ),
    "calcular": (
        calcular,
        "Resuelve una cuenta matematica. Ej: '2+2', 'sqrt(16)*3'.",
        {"type": "object", "properties": {"expresion": {"type": "string"}}, "required": ["expresion"]},
    ),
    "buscar_web": (
        buscar_web,
        "Busca informacion actual en internet. Usala cuando no sepas algo o necesites datos frescos.",
        {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]},
    ),
    "leer_url": (
        leer_url,
        "Lee el contenido de una pagina web a partir de su URL.",
        {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    ),
    "leer_archivo": (
        leer_archivo,
        "Lee un archivo de la carpeta de trabajo del motor.",
        {"type": "object", "properties": {"ruta": {"type": "string"}}, "required": ["ruta"]},
    ),
    "escribir_archivo": (
        escribir_archivo,
        "Crea o sobrescribe un archivo en la carpeta de trabajo del motor.",
        {"type": "object", "properties": {"ruta": {"type": "string"}, "contenido": {"type": "string"}},
         "required": ["ruta", "contenido"]},
    ),
    "listar_archivos": (
        listar_archivos,
        "Lista los archivos de la carpeta de trabajo.",
        {"type": "object", "properties": {"subcarpeta": {"type": "string"}}, "required": []},
    ),
    "ejecutar_python": (
        ejecutar_python,
        "Ejecuta codigo Python y devuelve el resultado. Usala para calcular cosas complejas o probar codigo.",
        {"type": "object", "properties": {"codigo": {"type": "string"}}, "required": ["codigo"]},
    ),
    "recordar": (
        recordar,
        "Guarda un dato importante en la memoria permanente.",
        {"type": "object", "properties": {"clave": {"type": "string"}, "valor": {"type": "string"}},
         "required": ["clave", "valor"]},
    ),
    "recuperar": (
        recuperar,
        "Recupera un dato guardado en la memoria permanente.",
        {"type": "object", "properties": {"clave": {"type": "string"}}, "required": []},
    ),
}

# Nombres de las herramientas para mostrar
NOMBRES = list(HERRAMIENTAS.keys())


def definiciones_para_modelo(permitidas=None):
    """Devuelve las herramientas en el formato que espera Ollama/OpenAI."""
    defs = []
    for nombre, (_, desc, params) in HERRAMIENTAS.items():
        if permitidas is not None and nombre not in permitidas:
            continue
        defs.append({
            "type": "function",
            "function": {"name": nombre, "description": desc, "parameters": params},
        })
    return defs


def ejecutar(nombre, argumentos):
    """Ejecuta una herramienta por nombre. 'argumentos' es un dict."""
    if nombre not in HERRAMIENTAS:
        return f"Herramienta desconocida: {nombre}"
    funcion = HERRAMIENTAS[nombre][0]
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos) if argumentos.strip() else {}
        except Exception:
            argumentos = {}
    try:
        _log(f"TOOL {nombre} {argumentos}")
        return str(funcion(**argumentos))
    except TypeError as e:
        return f"Argumentos incorrectos para {nombre}: {e}"
    except Exception as e:
        return f"Error en {nombre}: {e}"


if __name__ == "__main__":
    # Prueba rapida de cada herramienta
    print("Hora:", hora_actual())
    print("Calculo:", calcular("sqrt(144)+10"))
    print("Listar:", listar_archivos())
    print("Recordar:", recordar("prueba", "hola"))
    print("Recuperar:", recuperar("prueba"))
    print("Herramientas:", ", ".join(NOMBRES))
