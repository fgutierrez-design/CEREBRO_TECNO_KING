# MOTOR DE IA JARVIS — Guía completa (TECNO G)

Esta guía te lleva, paso a paso, desde cero hasta tener **tu propio motor de IA
funcionando en tu nube con GPU**, conectado a tu JARVIS del disco externo.

---

## 1. Qué es este motor y qué NO es

**Qué ES:** un motor de IA real, profesional y 100% tuyo. Corre un modelo abierto
(Qwen de Alibaba, gratis y libre) al que le pusimos tu personalidad. Piensa,
conversa, programa, busca en internet, escribe archivos, ejecuta código y recuerda.

**Qué NO es:** no es una copia del motor de ChatGPT, Gemini o del mío. Esos
modelos fueron entrenados con miles de GPUs, millones de dólares y petabytes de
datos. Eso no se puede clonar ni copiar. Lo que sí se puede —y es lo que hicimos—
es darte un motor propio, potente y gratuito, que hace el 90% de lo que necesitás.

---

## 2. Arquitectura (cómo encaja todo)

```
   TU PC (disco externo)                 TU NUBE (con GPU)
   ┌────────────────────┐                ┌──────────────────────────┐
   │  JARVIS (cerebro)  │  ── internet ─▶│  Ollama (el modelo)      │
   │  disco externo     │                │  puerto 11434            │
   │                    │                │                          │
   │  config_nube.json  │                │  servidor_motor.py       │
   │  motor_local.py    │  ── internet ─▶│  (API con herramientas)  │
   │  nube.py           │                │  puerto 11435            │
   │                    │                │                          │
   │                    │  ── internet ─▶│  servidor_conocimiento.py│
   │                    │                │  (memoria) puerto 8770   │
   └────────────────────┘                └──────────────────────────┘
```

- **Ollama (11434):** el modelo crudo (el que "piensa").
- **servidor_motor.py (11435):** la API con herramientas (el que "actúa").
- **servidor_conocimiento.py (8770):** guarda la memoria/conocimiento.

---

## 3. Requisitos

**En la nube (servidor):**
- Linux (Ubuntu/Debian recomendado) con acceso SSH.
- GPU con suficiente VRAM según el modelo que elijas.
- ~10-30 GB de disco libre.

**Guía de VRAM (modelo en 4 bits):**

| Modelo base          | VRAM aprox. | Calidad        | Ideal para            |
|----------------------|-------------|----------------|-----------------------|
| qwen2.5:1.5b         | ~1.5 GB     | básica         | pruebas               |
| qwen2.5:3b           | ~2.5 GB     | buena          | GPU chica             |
| qwen2.5:7b           | ~5 GB       | muy buena      | **recomendado**       |
| qwen2.5-coder:7b     | ~5 GB       | muy buena (cód)| programar             |
| qwen2.5:14b          | ~10 GB      | excelente      | GPU media             |
| qwen2.5:32b          | ~20 GB      | sobresaliente  | GPU grande            |

Si no sabés cuánta VRAM tenés, empezá con `qwen2.5:7b`.

---

## 4. Paso 1 — Subir el código a la nube

### Opción A: desde Windows (fácil)
1. Doble clic en **`SUBIR_A_LA_NUBE.bat`**.
2. Escribí el usuario, la IP de tu nube y (opcional) la carpeta destino.
3. Listo. El script copia todo por SSH.

> Si te dice que no encuentra `scp`, instalá OpenSSH (Panel de control →
> Aplicaciones → Características opcionales → Cliente OpenSSH) o usá **WinSCP**
> (arrastrás la carpeta y listo).

### Opción B: desde Linux/Mac
```bash
bash subir_a_la_nube.sh usuario@IP_DE_TU_NUBE /home/usuario/MOTOR_COMPLETO
```

### Opción C: a mano (con WinSCP o FileZilla)
Arrastrá toda la carpeta `MOTOR_COMPLETO` a tu servidor.

---

## 5. Paso 2 — Instalar en la nube (1 comando)

Conectate por SSH y corré el instalador:

```bash
ssh usuario@IP_DE_TU_NUBE
cd MOTOR_COMPLETO
bash instalar_motor.sh
```

El instalador hace **todo solo**:
1. Instala paquetes base (python, curl, git).
2. Instala Ollama.
3. Configura Ollama para escuchar en la red.
4. Baja el modelo base (por defecto `qwen2.5:7b`).
5. Crea tu motor **`jarvis-fer`** con tu personalidad.
6. Instala las dependencias de Python.
7. Deja los servicios **arrancando solos** (systemd).

Para elegir otro modelo base:
```bash
MODELO_BASE=qwen2.5-coder:7b bash instalar_motor.sh
```

---

## 6. Paso 3 — Probar que funciona

En la nube:
```bash
python3 cliente_prueba.py http://127.0.0.1:11435
```

Deberías ver respuestas en los puntos [3], [4] y [5]. Si los ves, **el motor anda**.

También podés probar directo el modelo:
```bash
ollama run jarvis-fer "Decime quién sos y para qué servís."
```

---

## 7. Paso 4 — Conectar tu JARVIS (disco externo)

En tu PC, abrí el archivo **`config_nube.json`** (está en la carpeta de JARVIS) y
poné la IP de tu nube. Hay dos formas:

### Forma segura (recomendada): túnel SSH
1. En `config_nube.json` dejá las URLs en `127.0.0.1` (como están).
2. Abrí una ventana y corré (o usá `tunel_ssh.bat`):
   ```
   ssh -L 11434:localhost:11434 -L 11435:localhost:11435 -L 8770:localhost:8770 usuario@IP_DE_TU_NUBE
   ```
3. Dejá esa ventana abierta. JARVIS se conecta por el túnel (nada expuesto a internet).

### Forma directa: IP pública
En `config_nube.json` cambiá:
```json
"url_motor": "http://IP_DE_TU_NUBE:11434",
"url_api_motor": "http://IP_DE_TU_NUBE:11435",
"url_conocimiento": "http://IP_DE_TU_NUBE:8770"
```
> ⚠️ Para esta forma, poné una **clave** y restringí los puertos en el firewall
> de tu proveedor SOLO a tu IP.

---

## 8. Seguridad (leelo, es importante)

Un motor abierto a internet lo puede usar cualquiera y te puede consumir la GPU.
Elegí UNA de estas:

- **Clave (fácil):** en la nube, `export JARVIS_MOTOR_CLAVE=tu_clave_secreta` y
  reiniciá el servicio (`sudo systemctl restart jarvis-motor`). Después poné esa
  misma clave en `config_nube.json`.
- **Túnel SSH (más seguro):** no expone nada a internet. Ver punto 7.
- **Firewall:** abrí los puertos 11434/11435/8770 SOLO a la IP de tu casa.

---

## 9. Cambiar el modelo o la personalidad

**Cambiar el modelo base** (por ejemplo a uno más grande):
```bash
bash descargar_modelo.sh qwen2.5:14b
```

**Cambiar la personalidad:** editá `Modelfile` (la sección `SYSTEM`) y recreá:
```bash
ollama create jarvis-fer -f Modelfile
```
También podés editar el campo `personalidad` de `config_motor.json`.

---

## 10. Comandos útiles (en la nube)

```bash
# Ver si el motor está vivo
sudo systemctl status jarvis-motor

# Reiniciar el motor
sudo systemctl restart jarvis-motor

# Ver los logs
sudo journalctl -u jarvis-motor -f

# Ver qué modelos tenés
ollama list

# Probar el modelo a mano
ollama run jarvis-fer
```

---

## 11. Preguntas frecuentes

**¿Es gratis?** El software sí (todo es libre). Solo pagás tu nube con GPU.

**¿Puedo tenerlo en mi PC en vez de la nube?** Sí. Corré `instalar_motor.sh` en
una PC con Linux, o instalá Ollama en Windows y usá `MOTOR_PROPIO/`.

**¿Se puede entrenar el modelo con MIS datos?** Sí, es el siguiente nivel
(fine-tuning). Se puede, pero necesita más GPU y tiempo. Este paquete te deja
listo el camino: primero usás el motor, después —si querés— lo afinás.

**¿Qué pasa si la nube se cae?** JARVIS sigue andando con lo que tenga local.
La nube es una mejora, no un requisito.

**¿Cuánto tarda la instalación?** Entre 10 y 30 minutos, casi todo es bajar el
modelo (depende de tu internet y del tamaño).

---

## 12. Estructura de archivos

```
MOTOR_COMPLETO/
├── LEEME_PRIMERO.txt          Empezá por acá
├── GUIA_COMPLETA.md           Esta guía
├── servidor_motor.py          Servidor de la API (puerto 11435)
├── motor_core.py              El cerebro (bucle agente)
├── herramientas.py            Las herramientas del motor
├── servidor_conocimiento.py   Servidor de memoria (puerto 8770)
├── cliente_prueba.py          Prueba el motor
├── Modelfile                  Personalidad del motor
├── config_motor.json          Configuración
├── requirements.txt           Dependencias Python
├── instalar_motor.sh          Instalador todo-en-uno (nube)
├── iniciar_motor.sh           Arrancar a mano
├── descargar_modelo.sh        Bajar/cambiar modelo
├── subir_a_la_nube.sh         Subir (Linux/Mac)
├── SUBIR_A_LA_NUBE.bat        Subir (Windows)
├── jarvis-motor.service       Servicio systemd (referencia)
├── Dockerfile                 Opción Docker
└── docker-compose.yml         Opción Docker Compose
```

---

**TECNO G — La Punta, San Luis, Argentina.**
