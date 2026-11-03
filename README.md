# Chatbot IA local multi-negocio

Backend en **FastAPI + SQLAlchemy (SQLite)** para un chatbot de atención al cliente que corre con un **LLM local** (sin APIs externas ni coste por token). Cada negocio tiene sus propias FAQs, tono y documentos, y el chat se incrusta en cualquier web con un widget de una línea.

## Qué hace

- **Chat por negocio** (`POST /chat`): responde con el LLM usando las FAQs del negocio, el historial de la sesión y fragmentos de sus documentos.
- **Atajos sin LLM**: si la pregunta pide información crítica (menú, clases, precios…) y hay una FAQ prioritaria, o se parece mucho a una FAQ, responde directamente. Más rápido y sin alucinaciones.
- **Carga de documentos** (`POST /api/train-ia`, PDF/DOCX hasta 20 MB): los trocea y genera FAQs automáticamente con el propio modelo.
- **Panel de administración** (`/admin.html`) y **widget embebible** (`frontend/widget.js`).
- **Dos backends de modelo**: `llama.cpp` (Meta-Llama 3.1 8B Q4_K_M, con GPU opcional) y GPT4All en CPU como respaldo.

## Estructura

```
chatbot/
├── backend/
│   ├── main.py                      # app FastAPI + CLI (--init-db, --host, --port)
│   ├── requirements.txt
│   └── app/
│       ├── api/routes/              # chat, businesses, faqs, documents, admin, system, demo
│       ├── services/
│       │   ├── chatbot_service.py   # carga del modelo, prompts, generate(), limpieza de respuestas
│       │   └── document_service.py  # extracción de texto, chunking, generación de FAQs
│       ├── models.py  schemas.py  database.py  config.py
├── frontend/                        # index.html, demo.html, admin.html, widget.js
└── run_backend_fixed.ps1            # arranque en Windows (venv + deps + servidor)
```

## Puesta en marcha

Desde la carpeta `chatbot/` (la que contiene `backend/`):

```bash
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Modelo: copia el .gguf a backend/models/
#   backend/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
# (o define CHATBOT_MODEL_NAME; sin modelo local se intenta orca-mini vía GPT4All)

ADMIN_API_KEY=cambia-esto python -m backend.main --host 0.0.0.0 --port 8000
```

En Windows, `./run_backend_fixed.ps1 -AdminKey 'cambia-esto'` hace lo mismo.

- Web de ejemplo: <http://localhost:8000/static/index.html> · Admin: <http://localhost:8000/admin.html> · Docs de la API: <http://localhost:8000/docs>
- Resetear la base de datos: borra `chatbot.db` y ejecuta `python -m backend.main --init-db`.

## Incrustar el widget

```html
<script>
  window.CHATBOT_API_URL = "http://localhost:8000";
  window.CHATBOT_BUSINESS_ID = 1;
</script>
<script src="http://localhost:8000/static/widget.js"></script>
```

Opcionales: `window.CHATBOT_POSITION` (`bottom-right`, `bottom-left`, `top-right`, `top-left`) y `window.CHATBOT_PRIMARY_COLOR`.

## Configuración (variables de entorno)

| Variable | Por defecto | Para qué |
|---|---|---|
| `ADMIN_API_KEY` | *(sin definir)* | Protege `/admin/*` y `/api/*` con la cabecera `X-API-KEY`. **Si no se define, esas rutas quedan abiertas** (solo desarrollo). |
| `DATABASE_URL` | `sqlite:///./chatbot.db` | Base de datos. |
| `CHATBOT_MODEL_NAME` | Llama 3.1 en `backend/models/` | Ruta o nombre del modelo. |
| `CHATBOT_BACKEND` | según el nombre del modelo | `meta-llama` (llama.cpp) o `gpt4all`. |
| `CHATBOT_PRELOAD` | `0` (`1` al lanzar con `python -m backend.main`) | Cargar el modelo al arrancar. |
| `LLAMA_N_THREADS` / `LLAMA_N_GPU_LAYERS` / `LLAMA_N_BATCH` | `8` / `40` / `512` | Ajustes de llama.cpp (`LLAMA_N_GPU_LAYERS=0` para CPU). |
| `CHATBOT_CONTEXT_WINDOW` | `4096` | Ventana de contexto del modelo (tokens). También vale `GPT4ALL_CONTEXT_WINDOW`. |
| `CHATBOT_CONTEXT_TOKEN_RATIO` | `3` | Caracteres por token que se asumen al recortar el prompt (español ≈ 3). |
| `CHATBOT_GENERATE_TIMEOUT` | `30` | Segundos máximos por respuesta del modelo (en CPU lenta, súbelo a 120–180). |
| `LLAMA_N_THREADS` | `8` | Hilos de CPU para llama.cpp; usa el número de núcleos físicos. |
| `CHATBOT_MAX_FAQS`, `CHATBOT_MAX_HISTORY_TURNS`, `CHATBOT_RESERVE_RESPONSE_TOKENS` | `4`, `4`, `200` | Tamaño del contexto enviado al modelo. |

## API principal

| Método y ruta | Descripción |
|---|---|
| `POST /chat` | Mensaje `{business_id, session_id, message}` → respuesta |
| `POST /chat/stream` | Igual que `/chat`, pero en streaming (SSE): eventos `{"delta": "..."}` y, al final, `{"final": "...", "done": true}` con el texto limpio |
| `GET/POST /businesses`, `GET/PUT/PATCH/DELETE /businesses/{id}` | Gestión de negocios |
| `GET/POST /faqs`, `GET /faqs/{business_id}`, `DELETE /faqs/{id}` | Gestión de FAQs |
| `GET /conversations/{business_id}` | Historial de conversaciones |
| `POST /api/train-ia` | Subir PDF/DOCX y generar FAQs |
| `GET /status`, `GET /health` | Estado del modelo y salud del servicio |
| `GET /admin/model_status`, `POST /admin/reinit_model`, `POST /admin/clear_model_failure` | Operaciones sobre el modelo |

## Rendimiento en CPU

El prompt (instrucciones + FAQs + historial) se procesa a ~40 tokens/s en una CPU modesta y el modelo escribe a ~7 tokens/s con un 8B Q4.
Las FAQs que entran en el contexto se eligen por relevancia con la pregunta. Para ir más rápido:

- Modelo más pequeño (p. ej. Llama 3.2 3B Instruct Q4_K_M, unas 2,5 veces más rápido): ponlo en `backend/models/` y define `CHATBOT_MODEL_NAME`.
- `CHATBOT_MAX_FAQS=2` y `LLAMA_N_THREADS` = núcleos físicos.
- Sube `CHATBOT_GENERATE_TIMEOUT` si tu equipo tarda más de 30 s.
