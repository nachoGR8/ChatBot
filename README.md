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
├── tests/                           # pytest (lógica + API con modelo falso)
├── eval/cases.json  scripts/        # casos de evaluación, eval.py, bench.py
deploy/                              # despliegue en VPS: Caddy + Docker, setup.sh, guía
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
<script>window.CHATBOT_BUSINESS_ID = 1;</script>
<script src="https://tu-servidor.com/widget.js"></script>
```

El widget usa como API el mismo servidor del que se carga el script y le pide el nombre y el mensaje de bienvenida del negocio,
así que no hay que repetirlos en cada web. `demo.html` e `index.html` usan este mismo widget; elige el negocio con `?business=ID`
(p. ej. `http://localhost:8000/demo.html?business=2`).

Opcionales: `window.CHATBOT_API_URL` (si la API está en otro servidor), `window.CHATBOT_POSITION`
(`bottom-right`, `bottom-left`, `top-right`, `top-left`) y `window.CHATBOT_PRIMARY_COLOR`.

## Configuración (variables de entorno)

| Variable | Por defecto | Para qué |
|---|---|---|
| `ADMIN_API_KEY` | *(sin definir)* | Clave del panel (cabecera `X-API-KEY`) para todas las rutas que modifican datos o leen conversaciones. **Si no se define, la administración queda deshabilitada (503)**, no abierta. |
| `CHATBOT_RATE_LIMIT_PER_MIN` | `20` | Mensajes por minuto e IP en `/chat` y `/chat/stream` (`0` = sin límite). Al superarlo: 429 con `Retry-After`. |
| `CHATBOT_TRUST_PROXY` | `0` | `1` si hay un proxy inverso delante (nginx, Caddy): la IP se toma de `X-Forwarded-For`. No lo actives sin proxy, o cualquiera podría falsear su IP. |
| `CHATBOT_CORS_ORIGINS` | `*` | Orígenes que pueden llamar a la API, separados por comas (p. ej. `https://minegocio.com`). |
| `CHATBOT_MAX_MESSAGE_CHARS` | `1000` | Longitud máxima de un mensaje del chat (422 si se supera). |
| `DATABASE_URL` | `sqlite:///./chatbot.db` | Base de datos. |
| `CHATBOT_MODEL_NAME` | Llama 3.1 en `backend/models/` | Ruta o nombre del modelo. |
| `CHATBOT_BACKEND` | según el nombre del modelo | `meta-llama` (llama.cpp) o `gpt4all`. |
| `CHATBOT_PRELOAD` | `0` (`1` al lanzar con `python -m backend.main`) | Cargar el modelo al arrancar. |
| `LLAMA_N_GPU_LAYERS` / `LLAMA_N_BATCH` | `40` / `512` | Capas en GPU (se ignora si llama.cpp es solo CPU) y tamaño de lote. |
| `CHATBOT_CONTEXT_WINDOW` | `4096` | Ventana de contexto del modelo (tokens). También vale `GPT4ALL_CONTEXT_WINDOW`. |
| `CHATBOT_CONTEXT_TOKEN_RATIO` | `3` | Caracteres por token que se asumen al recortar el prompt (español ≈ 3). |
| `CHATBOT_GENERATE_TIMEOUT` | `30` | Segundos máximos por respuesta del modelo (en CPU lenta, súbelo a 120–180). |
| `LLAMA_N_THREADS` | automático | Hilos para generar: todos los núcleos lógicos si son ≤ 4, la mitad si son más. Afínalo con `scripts/bench.py`. |
| `LLAMA_N_THREADS_BATCH` | = `LLAMA_N_THREADS` | Hilos para leer el prompt (la parte más lenta en CPU). |
| `LLAMA_FLASH_ATTN` | `0` | `1` activa flash attention en llama.cpp; mide con el benchmark si te compensa. |
| `CHATBOT_DOC_SNIPPETS` / `CHATBOT_DOC_SNIPPET_MAX_CHARS` | `2` / `350` | Fragmentos de documentos que entran en el prompt y su tamaño. |
| `CHATBOT_REPLY_CACHE_SIZE` | `128` | Respuestas guardadas en memoria por prompt exacto (`0` la desactiva). |
| `CHATBOT_MAX_FAQS`, `CHATBOT_MAX_HISTORY_TURNS`, `CHATBOT_RESERVE_RESPONSE_TOKENS` | `4`, `4`, `200` | Tamaño del contexto enviado al modelo. |

## API principal

| Método y ruta | Descripción |
|---|---|
| `POST /chat` | Mensaje `{business_id, session_id, message}` → respuesta |
| `POST /chat/stream` | Igual que `/chat`, pero en streaming (SSE): eventos `{"delta": "..."}` y, al final, `{"final": "...", "done": true}` con el texto limpio |
| `GET /businesses`, `GET /businesses/{id}` | Negocios (lectura pública) |
| `POST /businesses`, `PUT/PATCH/DELETE /businesses/{id}` 🔑 | Gestión de negocios |
| `GET /faqs?business_id=`, `GET /faqs/{business_id}` | FAQs (lectura pública) |
| `POST /faqs`, `DELETE /faqs/{id}` 🔑 | Gestión de FAQs |
| `GET /conversations/{business_id}` 🔑 | Historial de conversaciones (datos de los clientes) |
| `POST /api/train-ia` 🔑 | Subir PDF/DOCX y generar FAQs |
| `POST /seed-demo` 🔑 | Datos de ejemplo |
| `GET /status`, `GET /health` | Estado del modelo y salud del servicio |
| `GET /admin/model_status`, `POST /admin/reinit_model`, `POST /admin/clear_model_failure` 🔑 | Operaciones sobre el modelo |

🔑 = requiere la cabecera `X-API-KEY` con el valor de `ADMIN_API_KEY`.

## Rendimiento en CPU

En CPU, lo que más tarda es **leer el prompt** (~60 tokens/s en un portátil con un 8B Q4); escribir va a ~9 tokens/s.
Por eso el prompt está pensado para gastar poco:

- **Caché de prefijo de llama.cpp:** lo fijo de cada negocio (reglas, datos, tono) va delante y se reutiliza entre preguntas;
  lo que cambia (FAQs elegidas, documentos, historial) va al final y es lo único que se vuelve a procesar.
- **Solo lo relevante:** las FAQs se eligen por relevancia con la pregunta y de los documentos entran como mucho 2 fragmentos,
  recortados alrededor de las palabras de la pregunta (y ninguno si no hay coincidencias).
- **Caché de respuestas:** la misma pregunta en el mismo estado de conversación se responde al instante.
- **Streaming:** `/chat/stream` muestra el texto según se genera.
- **Calentamiento:** al cargar el modelo se hace una generación mínima (`CHATBOT_WARMUP=0` la desactiva) para que la primera pregunta real no pague la carga de pesos.
- **Respuesta directa por FAQ solo si coincide de verdad:** se comparan las palabras clave de la pregunta con las de la FAQ (umbral 0,85).

Medir en tu equipo (con el servidor en marcha):

```bash
python scripts/bench.py --business 1 "¿Quién es Ignacio?" "¿Qué tecnologías usa?"
```

Para ir más rápido: modelo más pequeño (p. ej. Llama 3.2 3B Instruct Q4_K_M, unas 2,5 veces más rápido).
Cópialo a `backend/models/` y arranca con `CHATBOT_MODEL_NAME=Llama-3.2-3B-Instruct-Q4_K_M.gguf` **y `CHATBOT_BACKEND=meta-llama`**
(el backend solo se deduce solo si el nombre del fichero contiene `meta-llama`). Además: `CHATBOT_MAX_FAQS=2`, y probar distintos `LLAMA_N_THREADS` con el benchmark.
Sube `CHATBOT_GENERATE_TIMEOUT` si tu equipo tarda más de 30 s.

## Docker

```bash
cp .env.example .env                      # edita ADMIN_API_KEY
# copia el .gguf a chatbot/backend/models/
docker compose up --build                 # http://localhost:8000/demo.html
```

El modelo no va en la imagen: se monta como volumen de solo lectura. La base de datos y los documentos persisten en volúmenes;
las tablas se crean solas al arrancar. La imagen compila llama.cpp para tu CPU (la primera vez tarda unos minutos).

**Publicarlo en un VPS con HTTPS:** ver [`deploy/README.md`](deploy/README.md). Un script (`deploy/setup.sh`) instala Docker,
descarga un modelo de 3B y lo arranca detrás de Caddy con certificado automático.

## Calidad: tests y evaluación

- **Tests** (`pytest`, sin modelo ni red: usan un LLM falso y SQLite temporal). Cubren la selección de FAQs, el umbral de coincidencia directa
  (con la regresión «estudios» ≠ «certificaciones»), el recorte de fragmentos, la caché LRU y los endpoints `/chat` y `/chat/stream`.
  Se ejecutan en GitHub Actions en cada push y PR.

  ```bash
  pip install -r backend/requirements-dev.txt
  python -m pytest
  ```

- **Evaluación con el modelo real** (servidor en marcha): `python scripts/eval.py --business 1 --out eval/results.md`.
  Cada caso de `eval/cases.json` comprueba que la respuesta no esté vacía, sea breve, hable en tercera persona, no filtre el prompt
  y contenga las palabras esperadas. Edita `expect_any` con datos de tu CV para que mida aciertos reales y guarda el informe resultante aquí.

## Decisiones de diseño

| Decisión | Motivo |
|---|---|
| LLM local con llama.cpp | Sin coste por token ni datos enviados a terceros; a cambio, hay que cuidar la latencia en CPU. |
| Prompt con prefijo fijo y parte variable al final | Reutiliza la caché KV de llama.cpp: solo se reprocesa lo que cambia. |
| FAQs y fragmentos elegidos por relevancia | Menos tokens = respuestas más rápidas y menos confusión del modelo. |
| Respuesta directa sin LLM si la FAQ coincide de verdad | Rápido y sin alucinaciones en datos críticos; el umbral evita falsos positivos. |
| Un lock alrededor de la generación | `llama_cpp.Llama` no es thread-safe; sin él, dos chats a la vez tumbaban el servidor. |
| Streaming SSE con texto final limpio | El usuario ve respuesta al instante y el cliente sustituye lo pintado por la versión depurada. |

## Límites conocidos

- Una sola generación a la vez (lock): pensado para demo/uso ligero, no para mucho tráfico concurrente.
- En CPU la primera palabra tarda segundos; con un modelo de 3B es unas 2,5 veces más rápida, a costa de calidad.
- El límite de mensajes vive en memoria: vale para un solo proceso; con varias réplicas haría falta Redis.
- SQLite y un único proceso: suficiente para una demo, no para producción con muchos negocios.

## Seguridad

- **Administración cerrada por defecto:** sin `ADMIN_API_KEY` no se puede crear, editar ni borrar nada (503). La clave se compara en tiempo constante.
- **Conversaciones protegidas:** `/conversations` contiene lo que escriben los clientes, así que exige la clave.
- **Límite de mensajes por IP** y **tamaño máximo de mensaje**: un único usuario no puede acaparar el modelo (que atiende de uno en uno) ni llenar su ventana de contexto.
- **CORS acotable** con `CHATBOT_CORS_ORIGINS`, y solo con los métodos y cabeceras que usa el frontend.
- Para publicarlo: pon un proxy con HTTPS delante (Caddy o nginx) con `CHATBOT_TRUST_PROXY=1`, usa una clave larga y no la subas al repositorio.
