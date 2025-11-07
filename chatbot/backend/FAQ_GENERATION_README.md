# Generación Automática de FAQs desde Documentos

## Descripción

Esta funcionalidad permite que la IA genere automáticamente preguntas frecuentes (FAQs) cuando se analiza un documento para entrenar el chatbot. Las FAQs se crean utilizando el modelo de lenguaje (LLM) y se almacenan en la base de datos para respuestas rápidas.

## Características

- ✅ **Generación Automática**: Al subir un documento PDF o DOCX, el sistema genera automáticamente entre 3-8 FAQs relevantes
- ✅ **Categorización**: Cada FAQ se categoriza automáticamente (información general, servicios, horarios, precios, etc.)
- ✅ **Integración con Negocios**: Las FAQs se asocian al negocio correspondiente
- ✅ **Trazabilidad**: Cada FAQ incluye una referencia al documento fuente
- ✅ **Prioridad Media**: Las FAQs generadas automáticamente tienen prioridad 5 (media) por defecto

## Cómo Funciona

### 1. Proceso de Ingesta de Documentos

Cuando subes un documento mediante el endpoint `/api/train-ia`:

```python
# Ejemplo de uso con curl
curl -X POST "http://localhost:8000/api/train-ia" \
  -H "X-API-Key: TU_API_KEY" \
  -F "files=@documento.pdf" \
  -F "business_id=1"
```

### 2. Flujo de Procesamiento

1. **Extracción de Texto**: El sistema extrae el texto del PDF o DOCX
2. **Normalización**: Limpia y formatea el texto
3. **Generación de Chunks**: Divide el texto en fragmentos para búsqueda
4. **Generación de FAQs**: 
   - Analiza el contenido del documento
   - Identifica información clave
   - Genera preguntas relevantes que un cliente haría
   - Crea respuestas basadas en el contenido
   - Asigna categorías apropiadas
5. **Almacenamiento**: Guarda las FAQs en la base de datos

### 3. Respuesta de la API

La respuesta incluye información sobre las FAQs creadas:

```json
{
  "ok": true,
  "documents_processed": 1,
  "business_id": 1,
  "results": [
    {
      "document_id": 123,
      "filename": "menu.pdf",
      "chunks_created": 5,
      "characters": 1250,
      "business_id": 1,
      "faqs_created": 6
    }
  ]
}
```

## Configuración del LLM

El sistema utiliza **la misma instancia del modelo LLM** que ya está cargada por el chatbot service. Esto significa:

- ✅ **No necesita cargar el modelo dos veces** (más eficiente en memoria)
- ✅ **Usa la misma configuración** (modelo, backend, GPU layers, etc.)
- ✅ **Compatible con llama_cpp y GPT4All** automáticamente
- ✅ **Aprovecha la GPU** si el chatbot está configurado para usarla

### Variables de Entorno Relevantes

```bash
# Modelo a utilizar
CHATBOT_MODEL_NAME="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Configuración de llama_cpp (si se usa Meta-Llama)
LLAMA_N_THREADS=8
LLAMA_N_GPU_LAYERS=40
LLAMA_N_BATCH=512
CHATBOT_CONTEXT_WINDOW=4096

# Configuración CUDA
GGML_CUDA_FORCE_CUBLAS=1
GGML_CUDA_FORCE_MMQ=1
```

El sistema detecta automáticamente el backend configurado (`llama_cpp` o `gpt4all`) y usa la API correspondiente.

## Estructura de las FAQs Generadas

Cada FAQ contiene:

- **question**: La pregunta (máximo 500 caracteres)
- **answer**: La respuesta basada en el documento (máximo 1000 caracteres)
- **category**: Categoría asignada automáticamente
- **priority**: Prioridad 5 (media) por defecto
- **business_id**: ID del negocio asociado
- **Referencia**: Enlace al documento fuente en la respuesta

### Ejemplo de FAQ Generada

```
Pregunta: "¿Cuál es el horario de atención del restaurante?"
Respuesta: "El restaurante está abierto de lunes a viernes de 12:00 PM a 10:00 PM, 
           y los sábados y domingos de 11:00 AM a 11:00 PM.

           [Fuente: Documento #123]"
Categoría: "horarios"
```

## Categorías Comunes

El sistema puede generar FAQs en las siguientes categorías (entre otras):

- `información general`: Información básica sobre el negocio
- `servicios`: Servicios ofrecidos
- `horarios`: Horarios de atención
- `precios`: Información de precios y tarifas
- `políticas`: Políticas del establecimiento
- `productos`: Productos disponibles
- `reservas`: Información sobre reservas
- `contacto`: Datos de contacto
- `documento`: Categoría por defecto

## Pruebas

### Ejecutar el Script de Prueba

```bash
# Navegar al directorio backend
cd chatbot/backend

# Ejecutar el script de prueba
python test_faq_generation.py
```

Este script:
1. Crea un texto de ejemplo (simulando un documento de restaurante)
2. Genera FAQs automáticamente
3. Muestra las FAQs generadas
4. Permite guardarlas en la base de datos

### Ver FAQs en la Base de Datos

```python
from app.database import SessionLocal
from app.models import FAQ, Business

db = SessionLocal()

# Ver todas las FAQs de un negocio
business_id = 1
faqs = db.query(FAQ).filter(FAQ.business_id == business_id).all()

for faq in faqs:
    print(f"[{faq.category}] {faq.question}")
    print(f"  → {faq.answer[:100]}...")
```

## Personalización

### Ajustar el Número de FAQs

Puedes modificar el prompt en `document_service.py`:

```python
# En el método _generate_faqs_from_text
prompt = f"""Analiza el siguiente documento{business_context} y genera entre 3 y 8 preguntas frecuentes...
```

Cambia "entre 3 y 8" al número deseado.

### Ajustar la Temperatura del LLM

```python
response = model.generate(
    prompt,
    max_tokens=800,
    temp=0.5,  # Ajustar entre 0.1 (más determinístico) y 1.0 (más creativo)
    top_p=0.9,
)
```

### Modificar la Prioridad de las FAQs

En `document_service.py`, método `_save_generated_faqs`:

```python
faq = FAQ(
    business_id=business.id,
    question=faq_data["question"],
    answer=answer_with_source,
    category=faq_data.get("category", "documento"),
    priority=5,  # Cambiar este valor (0-10)
)
```

## Resolución de Problemas

### No se generan FAQs

**Problema**: El sistema no genera FAQs al subir un documento.

**Soluciones**:
1. Verificar que el modelo LLM esté disponible:
   ```bash
   ls chatbot/backend/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
   ```

2. Revisar los logs:
   ```bash
   tail -f chatbot/logs/chatbot.log
   ```

3. Verificar que GPT4All esté instalado:
   ```bash
   pip list | grep gpt4all
   ```

### FAQs de baja calidad

**Problema**: Las FAQs generadas no son relevantes o útiles.

**Soluciones**:
1. Asegúrate de que el documento tenga contenido claro y estructurado
2. Ajusta la temperatura del modelo (menor = más conservador)
3. Mejora el prompt en `_generate_faqs_from_text`

### Error de memoria

**Problema**: El sistema se queda sin memoria al procesar documentos grandes.

**Soluciones**:
1. El sistema ya limita el texto a 3000 caracteres para la generación
2. Puedes reducir `max_text_length` en el método `_generate_faqs_from_text`
3. Reducir `max_tokens` en la generación

## Integración con el Frontend

### Mostrar FAQs Creadas

En tu interfaz de administración, puedes mostrar cuántas FAQs se crearon:

```javascript
// Después de subir un documento
fetch('/api/train-ia', {
    method: 'POST',
    headers: {
        'X-API-Key': 'TU_API_KEY'
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.ok) {
        data.results.forEach(result => {
            console.log(`Documento: ${result.filename}`);
            console.log(`Chunks creados: ${result.chunks_created}`);
            console.log(`FAQs generadas: ${result.faqs_created}`);
        });
    }
});
```

## Beneficios

1. **Ahorro de Tiempo**: No necesitas crear manualmente las FAQs
2. **Consistencia**: Las FAQs se generan con un formato consistente
3. **Cobertura**: Asegura que la información del documento esté disponible como FAQ
4. **Respuestas Rápidas**: El chatbot puede responder inmediatamente usando las FAQs
5. **Mejora Continua**: A medida que subes más documentos, la base de conocimiento crece

## Próximos Pasos

- [ ] Implementar validación de FAQs duplicadas
- [ ] Agregar opción para revisar/aprobar FAQs antes de guardar
- [ ] Permitir regenerar FAQs de documentos existentes
- [ ] Agregar embeddings para mejorar la búsqueda de FAQs similares
- [ ] Implementar analytics para ver qué FAQs son más útiles

## Soporte

Si tienes problemas o sugerencias, revisa los logs en `chatbot/logs/chatbot.log` o contacta al equipo de desarrollo.
