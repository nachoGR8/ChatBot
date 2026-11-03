FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# llama-cpp-python: rueda CPU precompilada (no hace falta compilador)
COPY backend/requirements.txt backend/requirements.txt
RUN grep -v -i "llama-cpp-python" backend/requirements.txt > /tmp/req.txt \
 && pip install -r /tmp/req.txt \
 && pip install --only-binary=:all: llama-cpp-python \
      --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

COPY backend backend
COPY frontend frontend

# El modelo .gguf NO va en la imagen: se monta como volumen en /app/backend/models
ENV DATABASE_URL=sqlite:////data/chatbot.db CHATBOT_PRELOAD=1
VOLUME ["/data"]
EXPOSE 8000
CMD ["python", "-m", "backend.main", "--host", "0.0.0.0", "--port", "8000"]
