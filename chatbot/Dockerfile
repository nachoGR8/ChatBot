# ---------- Etapa 1: compilar dependencias ----------
# llama-cpp-python no publica ruedas fiables para Linux: se compila aquí, en la máquina donde va a correr.
FROM python:3.12-slim AS build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential cmake git \
 && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# GGML_NATIVE=ON optimiza para la CPU de la máquina que construye (AVX2, NEON...).
# Si construyes la imagen en un equipo y la ejecutas en otro, usa: --build-arg LLAMA_CMAKE_ARGS="-DGGML_NATIVE=OFF"
ARG LLAMA_CMAKE_ARGS="-DGGML_NATIVE=ON"
ARG LLAMA_CPP_VERSION=0.3.36

COPY backend/requirements.txt /tmp/requirements.txt
# GPT4All es solo el respaldo para Windows sin llama.cpp: en el contenedor no hace falta.
RUN grep -viE "^(llama-cpp-python|gpt4all)" /tmp/requirements.txt > /tmp/req.txt \
 && pip wheel --wheel-dir /wheels -r /tmp/req.txt \
 && CMAKE_ARGS="$LLAMA_CMAKE_ARGS" pip wheel --wheel-dir /wheels "llama-cpp-python==${LLAMA_CPP_VERSION}"

# ---------- Etapa 2: imagen final (sin compiladores) ----------
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY --from=build /wheels /wheels
RUN pip install --no-index /wheels/*.whl && rm -rf /wheels

RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY backend backend
COPY frontend frontend
# /data: base de datos · storage: documentos subidos · logs · models: el .gguf se monta como volumen (no va en la imagen)
RUN mkdir -p /data storage logs backend/models && chown -R app:app /data storage logs

USER app
ENV DATABASE_URL=sqlite:////data/chatbot.db \
    CHATBOT_PRELOAD=1 \
    LLAMA_N_GPU_LAYERS=0
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["python", "-m", "backend.main", "--host", "0.0.0.0", "--port", "8000"]
