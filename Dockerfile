# ============================================================
#  Dockerfile  -  Motor JARVIS en contenedor (opcion avanzada)
#
#  Este contenedor levanta la API del motor.
#  Ollama corre aparte (ver docker-compose.yml).
# ============================================================
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requisitos.txt ./
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir -r requisitos.txt
COPY . .
ENV PORT=10000
ENV JARVIS_MOTOR_PUERTO=10000
EXPOSE 10000
CMD ["python", "servidor_motor.py"]
