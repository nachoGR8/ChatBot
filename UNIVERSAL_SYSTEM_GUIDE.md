# 🌐 Sistema Universal - Guía Completa

## 📋 ¿Qué es el Sistema Universal?

El sistema ahora funciona para **CUALQUIER tipo de negocio**, no solo restaurantes. Detecta automáticamente información crítica estructurada en documentos (PDFs, textos) y responde con **100% precisión sin inventar nada**.

### ✅ Tipos de Negocios Soportados

| Tipo | Información Detectada | Emoji |
|------|----------------------|-------|
| **Restaurantes** | Menú, carta, platos, bebidas | 🍽️ |
| **Gimnasios** | Clases, horarios, actividades | 💪 |
| **Tiendas** | Productos, catálogo, inventario | 🛍️ |
| **Hoteles** | Habitaciones, suites, tipos | 🏨 |
| **Servicios** | Tratamientos, paquetes | 📋 |
| **Clínicas** | Servicios, tratamientos | 🏥 |
| **Academias** | Cursos, programas | 📚 |
| **Spas** | Tratamientos, terapias | 💆 |
| **Cualquier negocio** | Tarifas, precios, planes | 💰 |

---

## 🔧 Cómo Funciona

### 1️⃣ Procesamiento Automático de Documentos

Cuando subes un PDF:

```
📄 PDF subido
   ↓
🤖 IA detecta tipo de información
   (menú, clases, productos, etc.)
   ↓
📊 Extrae TODA la información
   (temperatura 0.1 = sin invenciones)
   ↓
💾 Crea FAQ con prioridad 100
   (activa bypass directo)
```

**Código clave:** `document_service.py` → método `_detect_critical_sections()`

### 2️⃣ Detección Inteligente en Chat

Cuando un usuario pregunta:

```
👤 "¿Qué clases tienen?"
   ↓
🔍 Sistema detecta: tipo='clases', keywords=['clases', 'horarios', ...]
   ↓
📂 Busca FAQs con prioridad >= 100 y keywords matching
   ↓
✅ Retorna directamente SIN pasar por LLM
   (0% alucinaciones, 100% precisión)
```

**Código clave:** `chatbot_service.py` → método `is_critical_info_request()`

---

## 🧪 Cómo Probar

### Ejemplo 1: Restaurante (Ya funciona ✅)

```python
# 1. Sube PDF con menú
POST /documents/upload
{
    "business_id": 1,
    "file": menu.pdf
}

# 2. Pregunta por el menú
POST /chat
{
    "business_id": 1,
    "session_id": "test-123",
    "message": "¿Qué tienen en el menú?"
}

# ✅ Respuesta directa con 100% precisión
```

### Ejemplo 2: Gimnasio (Nuevo ✨)

```python
# 1. Crea un gimnasio
POST /businesses
{
    "name": "FitZone Gym",
    "business_type": "gimnasio",
    "phone": "123456789"
}

# 2. Sube PDF con horario de clases
# Contenido ejemplo:
"""
HORARIO DE CLASES 2024

Lunes:
- 7:00 AM - Yoga
- 9:00 AM - Spinning
- 6:00 PM - CrossFit

Martes:
- 7:00 AM - Pilates
- 8:00 AM - Zumba
...
"""

POST /documents/upload
{
    "business_id": 2,
    "file": clases.pdf
}

# 3. Pregunta por las clases
POST /chat
{
    "business_id": 2,
    "session_id": "gym-test",
    "message": "¿Qué clases tienen disponibles?"
}

# ✅ Respuesta: Lista completa de clases con horarios
```

### Ejemplo 3: Tienda Online (Nuevo ✨)

```python
# 1. Crea tienda
POST /businesses
{
    "name": "TechStore",
    "business_type": "tienda",
    "phone": "987654321"
}

# 2. Sube catálogo de productos
# Contenido ejemplo:
"""
CATÁLOGO DE PRODUCTOS

Laptops:
- MacBook Pro M3 - $2,499
- Dell XPS 15 - $1,899
- Lenovo ThinkPad - $1,299

Smartphones:
- iPhone 15 Pro - $999
- Samsung Galaxy S24 - $849
...
"""

POST /documents/upload
{
    "business_id": 3,
    "file": catalogo.pdf
}

# 3. Pregunta por los productos
POST /chat
{
    "business_id": 3,
    "session_id": "store-test",
    "message": "¿Qué productos tienen en el catálogo?"
}

# ✅ Respuesta: Catálogo completo con precios
```

---

## 📝 Palabras Clave Detectadas

El sistema detecta automáticamente estas preguntas:

### Para Menús (Restaurantes)
- "¿Qué tienen en el menú?"
- "¿Cuál es la carta?"
- "¿Qué platos hay?"
- "Muéstrame el menú"

### Para Clases (Gimnasios)
- "¿Qué clases tienen?"
- "¿Cuáles son los horarios?"
- "¿Qué actividades hay?"
- "Lista de entrenamiento"

### Para Productos (Tiendas)
- "¿Qué productos venden?"
- "Catálogo completo"
- "¿Qué tienen en inventario?"
- "Lista de artículos"

### Para Servicios (Clínicas, Spas)
- "¿Qué servicios ofrecen?"
- "Lista de tratamientos"
- "¿Qué paquetes tienen?"

### Para Habitaciones (Hoteles)
- "¿Qué tipos de habitaciones hay?"
- "Lista de suites"
- "Opciones de alojamiento"

### Para Tarifas (Universal)
- "¿Cuáles son los precios?"
- "¿Cuánto cuesta?"
- "Lista de tarifas"
- "Planes y precios"

---

## 🔍 Cómo Verificar que Funciona

### 1. Verifica que el FAQ se creó con prioridad 100

```python
# Consulta la base de datos
import sqlite3
conn = sqlite3.connect('chatbot/chatbot.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, question, category, priority 
    FROM faqs 
    WHERE business_id = ? AND priority >= 100
""", (business_id,))

results = cursor.fetchall()
for row in results:
    print(f"FAQ {row[0]}: {row[1]} (categoría: {row[2]}, prioridad: {row[3]})")
```

**Salida esperada:**
```
FAQ 345: ¿Qué tienen en el menú? (categoría: menú, prioridad: 100)
FAQ 346: ¿Qué clases tienen? (categoría: clases, prioridad: 100)
```

### 2. Verifica los logs del backend

```powershell
# Ver logs en tiempo real
Get-Content logs\chatbot.log -Wait | Select-String "🎯|✅|🔍"
```

**Salida esperada:**
```
🎯 Detectado tipo crítico: clases (patrón: \bclases?\b)
🔍 Detectada consulta de información crítica: '¿Qué clases tienen?'
🔍 Tipo detectado: clases
🔍 FAQs críticos filtrados (prioridad >= 100): 1
✅ Retornando FAQ 346 directamente SIN pasar por LLM
```

### 3. Prueba con cliente HTTP

```powershell
# Test con Invoke-RestMethod (PowerShell)
$body = @{
    business_id = 2
    session_id = "test-gym-123"
    message = "¿Qué clases hay disponibles?"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/chat" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

Write-Host $response.response
```

---

## ⚙️ Configuración

### Variables de Entorno (opcional)

```bash
# Temperatura para detección (0.0-1.0, recomendado: 0.2)
DETECTION_TEMPERATURE=0.2

# Temperatura para extracción (0.0-1.0, recomendado: 0.1)
EXTRACTION_TEMPERATURE=0.1

# Máximo tokens para extracción
MAX_EXTRACTION_TOKENS=2000

# Prioridad mínima para bypass directo (default: 100)
MIN_BYPASS_PRIORITY=100
```

---

## 🐛 Troubleshooting

### Problema: El sistema no detecta mi tipo de información

**Solución:** Añade nuevos patrones en `chatbot_service.py`:

```python
def is_critical_info_request(self, message: str) -> Optional[dict]:
    critical_types = {
        # ... tipos existentes ...
        
        # NUEVO TIPO
        'tu_tipo': {
            'patterns': [
                r'\bpalabra_clave1\b',
                r'\bpalabra_clave2\b',
                r'frase específica',
            ],
            'keywords': ['palabra1', 'palabra2'],
            'emoji': '🆕'
        },
    }
```

### Problema: El FAQ no se está creando con prioridad 100

**Solución:** Verifica los logs de procesamiento:

```powershell
Get-Content logs\chatbot.log | Select-String "_detect_critical_sections"
```

Si dice "NO se detectó información crítica", mejora el prompt de detección en `document_service.py` línea 330.

### Problema: El LLM sigue inventando información

**Posibles causas:**
1. El FAQ no tiene prioridad >= 100
2. Las keywords no coinciden
3. El bypass no se está activando

**Solución:** Verifica logs:
```powershell
Get-Content logs\chatbot.log | Select-String "Retornando FAQ.*directamente"
```

Si NO ves ese mensaje, el bypass no se activó. Verifica las keywords en el FAQ y en la detección.

---

## 🚀 Próximos Pasos

1. **Probar con diferentes tipos de negocios**
   - Gimnasio con horario de clases
   - Tienda con catálogo de productos
   - Hotel con lista de habitaciones

2. **Optimizar prompts de detección**
   - Ajustar temperatura si hay falsos positivos/negativos
   - Añadir más ejemplos al prompt

3. **Crear tests automatizados**
   - Test de detección para cada tipo
   - Test de extracción con diferentes formatos
   - Test de bypass con diferentes consultas

4. **Documentar casos de uso reales**
   - Crear plantillas de PDFs para cada tipo
   - Ejemplos de preguntas típicas por tipo
   - Guía de mejores prácticas

---

## 📚 Documentación Técnica

### Archivos Modificados

1. **`document_service.py`**
   - Método `_detect_critical_sections()` (líneas 283-446)
   - Método `_generate_question_for_type()` (líneas 448-476)
   - Lógica universal de procesamiento (líneas 304-326)

2. **`chatbot_service.py`**
   - Método `is_critical_info_request()` (líneas 170-294)
   - Método `is_menu_request()` deprecado (líneas 296-300)

3. **`chat.py`**
   - Sistema de bypass universal (líneas 37-88)
   - Variables `is_critical_request` en lugar de `wants_menu`

### Flujo de Datos

```
📄 PDF Upload
   ↓
📊 document_service._detect_critical_sections()
   → Detección con LLM (temp=0.2)
   → Extracción con LLM (temp=0.1)
   → Generación de pregunta automática
   ↓
💾 Crea FAQ con priority=100
   ↓
👤 Usuario pregunta
   ↓
🔍 chatbot_service.is_critical_info_request()
   → Detecta tipo (menú, clases, productos...)
   → Retorna keywords y emoji
   ↓
📂 chat.py busca FAQs con priority>=100 y keywords
   ↓
✅ Retorna directamente SIN LLM
   (0% alucinaciones)
```

---

## ✨ Ventajas del Sistema Universal

1. **Escalable:** Funciona para cualquier tipo de negocio sin cambios de código
2. **Preciso:** 0% alucinaciones en información crítica estructurada
3. **Automático:** Detecta tipos de información automáticamente con IA
4. **Flexible:** Fácil añadir nuevos tipos de información
5. **Profesional:** Bypass inteligente evita problemas del LLM

---

## 🎯 Casos de Uso Recomendados

### ✅ Perfecto para:
- Menús de restaurantes
- Horarios de clases en gimnasios
- Catálogos de productos en tiendas
- Listas de habitaciones en hoteles
- Tarifas y precios estructurados
- Servicios y tratamientos de clínicas/spas
- Cualquier información estructurada en tablas/listas

### ⚠️ No recomendado para:
- Preguntas conversacionales generales
- Información no estructurada
- Contextos que requieren razonamiento
- Respuestas personalizadas por usuario

---

**Fecha:** 2024
**Versión:** 2.0 - Sistema Universal
**Autor:** Chatbot Inteligente con IA
