# Resumen de Cambios - Generación Automática de FAQs

## 📋 Descripción General

Se ha implementado la funcionalidad de generación automática de FAQs cuando se analizan documentos para entrenar la IA. Esta característica utiliza el modelo LLM (GPT4All) para crear preguntas frecuentes basadas en el contenido de los documentos subidos.

## 🔧 Archivos Modificados

### 1. `backend/app/services/document_service.py`
**Cambios principales:**

- ✅ Agregado import de modelo `FAQ`
- ✅ Actualizado `IngestResult` dataclass con campo `faqs_created`
- ✅ Nuevo método `_generate_faqs_from_text()`: Genera FAQs usando el LLM
- ✅ Nuevo método `_save_generated_faqs()`: Guarda las FAQs en la base de datos
- ✅ Modificado `ingest_upload()`: Integra la generación de FAQs en el flujo de procesamiento

**Funcionalidades añadidas:**

```python
def _generate_faqs_from_text(text: str, business: Optional[Business]) -> List[Dict[str, str]]
```
- **Reutiliza el modelo LLM ya cargado** por chatbot_service (no carga uno nuevo)
- **Compatible con llama_cpp y GPT4All** automáticamente
- Analiza el contenido del documento
- Genera entre 3-8 FAQs relevantes
- Categoriza automáticamente cada FAQ
- Limita el texto a 2500 caracteres para optimizar el procesamiento
- **Aprovecha la GPU** si está configurada en el chatbot

```python
def _save_generated_faqs(db: Session, faqs: List[Dict], business: Business, document_id: int) -> int
```
- Guarda las FAQs generadas en la base de datos
- Asocia las FAQs al negocio correspondiente
- Agrega referencia al documento fuente
- Asigna prioridad media (5) por defecto

## 📁 Archivos Nuevos Creados

### 2. `backend/test_faq_generation.py`
Script de prueba para verificar la generación de FAQs:
- Usa texto de ejemplo de un restaurante
- Muestra las FAQs generadas
- Permite guardar en la base de datos
- Útil para desarrollo y debugging

### 3. `backend/FAQ_GENERATION_README.md`
Documentación completa que incluye:
- Descripción de la funcionalidad
- Cómo funciona el proceso
- Ejemplos de uso
- Configuración del LLM
- Estructura de las FAQs
- Guía de resolución de problemas
- Ejemplos de integración con frontend

### 4. `frontend/demo_faq_generation.html`
Demo visual interactiva que muestra:
- Interfaz de carga de documentos
- Visualización de resultados
- Ejemplo de FAQs generadas
- Diseño moderno y responsivo

## 🚀 Características Implementadas

### Generación Automática
- ✅ 3-8 FAQs por documento
- ✅ Categorización inteligente
- ✅ Respuestas basadas en el contenido
- ✅ Referencia al documento fuente

### Integración con API
- ✅ El endpoint `/api/train-ia` ahora retorna `faqs_created`
- ✅ Compatible con documentos PDF y DOCX
- ✅ Asociación con negocios
- ✅ Manejo de errores robusto

### Categorías Automáticas
El sistema puede generar FAQs en categorías como:
- `información general`
- `servicios`
- `horarios`
- `precios`
- `políticas`
- `productos`
- `reservas`
- `contacto`

## 📊 Ejemplo de Respuesta API

Antes:
```json
{
  "document_id": 123,
  "filename": "menu.pdf",
  "chunks_created": 5,
  "characters": 1250,
  "business_id": 1
}
```

Después:
```json
{
  "document_id": 123,
  "filename": "menu.pdf",
  "chunks_created": 5,
  "characters": 1250,
  "business_id": 1,
  "faqs_created": 6
}
```

## 🔍 Flujo de Procesamiento

```
1. Usuario sube documento (PDF/DOCX)
         ↓
2. Sistema extrae y normaliza texto
         ↓
3. Crea chunks para búsqueda
         ↓
4. 🆕 Genera FAQs con LLM
         ↓
5. 🆕 Guarda FAQs en base de datos
         ↓
6. Retorna resultados (incluyendo faqs_created)
```

## 📝 Ejemplo de FAQ Generada

```
Pregunta: "¿Cuál es el horario de atención del restaurante?"

Respuesta: "El restaurante está abierto de lunes a viernes de 
12:00 PM a 10:00 PM, y los sábados y domingos de 11:00 AM a 11:00 PM.

[Fuente: Documento #123]"

Categoría: "horarios"
Prioridad: 5
```

## 🎯 Beneficios

1. **Ahorro de Tiempo**: No se necesitan crear FAQs manualmente
2. **Consistencia**: Formato uniforme en todas las FAQs
3. **Cobertura**: Información del documento disponible inmediatamente
4. **Respuestas Rápidas**: El chatbot puede responder usando las FAQs
5. **Escalabilidad**: Crece automáticamente con cada documento

## ⚙️ Configuración Necesaria

### Modelo LLM
El sistema requiere el modelo LLM configurado:
```bash
# Variable de entorno (opcional)
CHATBOT_MODEL_NAME="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# O usar la ubicación por defecto:
# chatbot/backend/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

### Dependencias
Ya instaladas en el proyecto:
- `gpt4all`: Para el modelo LLM
- `sqlalchemy`: Para la base de datos
- `pypdf2`: Para PDFs
- `python-docx`: Para DOCX

## 🧪 Cómo Probar

### 1. Ejecutar el Script de Prueba
```bash
cd chatbot/backend
python test_faq_generation.py
```

### 2. Probar con la API
```bash
curl -X POST "http://localhost:8000/api/train-ia" \
  -H "X-API-Key: TU_API_KEY" \
  -F "files=@documento.pdf" \
  -F "business_id=1"
```

### 3. Ver la Demo Visual
```bash
# Abrir en el navegador:
chatbot/frontend/demo_faq_generation.html
```

## 🔄 Próximas Mejoras (Opcionales)

- [ ] Validación de FAQs duplicadas
- [ ] Opción para revisar antes de guardar
- [ ] Regenerar FAQs de documentos existentes
- [ ] Embeddings para búsqueda semántica
- [ ] Analytics de FAQs más útiles
- [ ] Edición manual de FAQs generadas
- [ ] Exportar FAQs a diferentes formatos

## 📖 Documentación

Para más detalles, consultar:
- `FAQ_GENERATION_README.md`: Documentación completa
- `test_faq_generation.py`: Ejemplos de uso
- `demo_faq_generation.html`: Demo visual

## ✅ Estado

- ✅ Implementación completa
- ✅ Sin errores de sintaxis
- ✅ Documentación incluida
- ✅ Scripts de prueba creados
- ✅ Demo visual disponible
- ⏳ Pendiente de pruebas en producción

## 👤 Uso

La funcionalidad está lista para usar. Simplemente sube un documento a través del endpoint `/api/train-ia` y el sistema generará automáticamente las FAQs asociadas al negocio.

---

**Fecha de implementación**: 7 de octubre, 2025
**Versión**: 1.0
**Estado**: Listo para pruebas
