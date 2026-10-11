# ============================================================
#  Dockerfile  -  Motor JARVIS en contenedor (opcion avanzada)
#
#  Este contenedor levanta la API del motor.
#  Ollama corre aparte (ver docker-compose.yml).
# ============================================================
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV JARVIS_MOTOR_PUERTO=11435
ENV OLLAMA_URL=http://ollama:11434
EXPOSE 11435

CMD ["python", "servidor_motor.py"]
