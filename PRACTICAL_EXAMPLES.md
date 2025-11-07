# 🎬 Ejemplos Prácticos - Sistema Universal

## 📚 Escenarios de Uso Real

---

## Ejemplo 1: Gimnasio con Horario de Clases

### 📄 Documento: `horario_fitness_2024.pdf`

```
═══════════════════════════════════════════════════════════
              FITZONE GYM - HORARIO DE CLASES
                      ENERO 2024
═══════════════════════════════════════════════════════════

LUNES
─────────────────────────────────────────────────────────
07:00 - 08:00 | Yoga Flow         | Instructor: María    | Sala 1
09:00 - 10:00 | Spinning Intenso  | Instructor: Carlos   | Sala 2
10:00 - 11:00 | Pilates Reformer  | Instructor: Ana      | Sala 3
18:00 - 19:00 | CrossFit          | Instructor: Pedro    | Sala 2
19:00 - 20:00 | Zumba             | Instructor: Laura    | Sala 1

MARTES
─────────────────────────────────────────────────────────
07:00 - 08:00 | Power Yoga        | Instructor: María    | Sala 1
09:00 - 10:00 | Body Pump         | Instructor: Carlos   | Sala 2
10:00 - 11:00 | Stretching        | Instructor: Ana      | Sala 3
18:00 - 19:00 | Boxing            | Instructor: Pedro    | Sala 2
19:00 - 20:00 | Salsa Fitness     | Instructor: Laura    | Sala 1

MIÉRCOLES
─────────────────────────────────────────────────────────
07:00 - 08:00 | Yoga Restaurativo | Instructor: María    | Sala 1
09:00 - 10:00 | Cycling           | Instructor: Carlos   | Sala 2
10:00 - 11:00 | Pilates Mat       | Instructor: Ana      | Sala 3
18:00 - 19:00 | Funcional         | Instructor: Pedro    | Sala 2
19:00 - 20:00 | Baile Latino      | Instructor: Laura    | Sala 1

═══════════════════════════════════════════════════════════
         CLASES ESPECIALES DE FIN DE SEMANA
═══════════════════════════════════════════════════════════

SÁBADO
─────────────────────────────────────────────────────────
09:00 - 10:30 | Yoga + Meditación  | María & Ana         | Sala 1
11:00 - 12:00 | HIIT               | Carlos & Pedro      | Sala 2

DOMINGO
─────────────────────────────────────────────────────────
10:00 - 11:30 | Clase Familiar     | Todo el equipo      | Todas

═══════════════════════════════════════════════════════════
NOTA: Las clases tienen cupo limitado. 
Reserva con 24h de anticipación en recepción.
═══════════════════════════════════════════════════════════
```

### 🤖 Configuración del Sistema

```python
# 1. Crear el gimnasio
POST http://localhost:8000/businesses
Content-Type: application/json

{
    "name": "FitZone Gym",
    "business_type": "gimnasio",
    "phone": "555-0123",
    "email": "info@fitzonegym.com",
    "address": "Av. Principal 123",
    "description": "El mejor gimnasio de la ciudad con clases para todos los niveles"
}

# Response: {"id": 2, ...}
```

```python
# 2. Subir el horario
POST http://localhost:8000/documents/upload
Content-Type: multipart/form-data

business_id=2
file=@horario_fitness_2024.pdf
```

### 💬 Conversaciones Esperadas

**Consulta 1:**
```
👤 Usuario: "¿Qué clases tienen disponibles?"

🤖 Bot: "¡Hola! 💪 Con mucho gusto te muestro la información:

═══════════════════════════════════════════════════════════
              FITZONE GYM - HORARIO DE CLASES
                      ENERO 2024
═══════════════════════════════════════════════════════════

LUNES
─────────────────────────────────────────────────────────
07:00 - 08:00 | Yoga Flow         | Instructor: María    | Sala 1
09:00 - 10:00 | Spinning Intenso  | Instructor: Carlos   | Sala 2
[...resto del horario completo...]"
```

**Consulta 2:**
```
👤 Usuario: "Horarios de clases por la mañana"

🤖 Bot: [Responde con el horario completo desde el FAQ, incluye todo]
```

**Consulta 3:**
```
👤 Usuario: "¿Tienen yoga?"

🤖 Bot: [Usa el LLM normal para responder específicamente sobre yoga,
         basándose en el contexto del FAQ de clases]
```

---

## Ejemplo 2: Tienda Online con Catálogo

### 📄 Documento: `catalogo_techstore_2024.pdf`

```
═══════════════════════════════════════════════════════════
                    TECHSTORE
            CATÁLOGO DE PRODUCTOS 2024
═══════════════════════════════════════════════════════════

💻 LAPTOPS
─────────────────────────────────────────────────────────

📱 MacBook Pro 16" M3
   • Chip M3 Pro / 36GB RAM / 1TB SSD
   • Pantalla Retina XDR
   • Batería 22 horas
   • Color: Space Black, Silver
   💰 Precio: $2,499

📱 Dell XPS 15 (2024)
   • Intel Core i9-13900H / 32GB RAM / 1TB SSD
   • Pantalla OLED 4K Touch
   • NVIDIA RTX 4060
   • Color: Platinum Silver
   💰 Precio: $1,899

📱 Lenovo ThinkPad X1 Carbon Gen 11
   • Intel Core i7-1365U / 16GB RAM / 512GB SSD
   • Pantalla 14" 2.8K
   • Ultraligera 1.12kg
   • Color: Black
   💰 Precio: $1,299

📱 ASUS ROG Strix G16
   • Intel Core i9-13980HX / 32GB RAM / 2TB SSD
   • Pantalla 16" QHD 240Hz
   • NVIDIA RTX 4070
   • RGB Aura Sync
   💰 Precio: $2,199

═══════════════════════════════════════════════════════════

📱 SMARTPHONES
─────────────────────────────────────────────────────────

📱 iPhone 15 Pro Max
   • A17 Pro / 256GB / 8GB RAM
   • Cámara 48MP + Teleobjetivo 5x
   • Titanio + USB-C
   • Color: Natural, Blue, White, Black
   💰 Precio: $1,199

📱 Samsung Galaxy S24 Ultra
   • Snapdragon 8 Gen 3 / 256GB / 12GB RAM
   • S Pen incluido
   • Cámara 200MP
   • Color: Titanium Gray, Violet, Yellow
   💰 Precio: $1,299

📱 Google Pixel 8 Pro
   • Tensor G3 / 128GB / 12GB RAM
   • IA avanzada
   • Cámara Magic Eraser
   • Color: Obsidian, Porcelain, Bay
   💰 Precio: $999

═══════════════════════════════════════════════════════════

⌚ SMARTWATCHES
─────────────────────────────────────────────────────────

⌚ Apple Watch Ultra 2
   • GPS + Cellular / 49mm Titanio
   • Pantalla Always-On más brillante
   • Resistencia extrema
   💰 Precio: $799

⌚ Samsung Galaxy Watch 6 Classic
   • 43mm / Bluetooth + WiFi
   • Bisel giratorio
   • Monitoreo avanzado de salud
   💰 Precio: $399

═══════════════════════════════════════════════════════════

🎧 AUDIO
─────────────────────────────────────────────────────────

🎧 AirPods Pro (2ª Gen)
   • Cancelación de ruido adaptativa
   • Audio espacial
   • Estuche MagSafe USB-C
   💰 Precio: $249

🎧 Sony WH-1000XM5
   • Cancelación de ruido líder
   • 30h de batería
   • Hi-Res Audio
   💰 Precio: $399

═══════════════════════════════════════════════════════════
ENVÍO GRATIS en compras mayores a $100
GARANTÍA de 2 años en todos los productos
DEVOLUCIÓN dentro de 30 días
═══════════════════════════════════════════════════════════
```

### 🤖 Configuración

```python
# 1. Crear la tienda
POST http://localhost:8000/businesses
{
    "name": "TechStore",
    "business_type": "tienda",
    "phone": "555-9876",
    "email": "ventas@techstore.com",
    "address": "Centro Comercial Plaza Tech, Local 45"
}

# 2. Subir catálogo
POST http://localhost:8000/documents/upload
business_id=3
file=@catalogo_techstore_2024.pdf
```

### 💬 Conversaciones

```
👤 "¿Qué productos tienen?"
🤖 [Responde con catálogo completo] 🛍️

👤 "Cuánto cuesta el iPhone 15 Pro Max"
🤖 [Busca en el contexto y responde: "$1,199"] 💰

👤 "Necesito una laptop para gaming"
🤖 [Recomienda ASUS ROG o Dell XPS con specs] 🎮
```

---

## Ejemplo 3: Hotel con Tipos de Habitaciones

### 📄 Documento: `habitaciones_hotel_paradise.pdf`

```
═══════════════════════════════════════════════════════════
                  HOTEL PARADISE
            TIPOS DE HABITACIONES 2024
═══════════════════════════════════════════════════════════

🏨 STANDARD ROOM
─────────────────────────────────────────────────────────
✓ Superficie: 20m²
✓ Cama: 1 matrimonial o 2 individuales
✓ Vista: Ciudad
✓ Capacidad: 2 personas
✓ Servicios incluidos:
  • WiFi gratuito
  • TV LCD 32"
  • Aire acondicionado
  • Minibar
  • Baño privado con ducha
  • Desayuno buffet

💰 TARIFA: $80/noche
   (Temporada baja: $65/noche)

═══════════════════════════════════════════════════════════

🏨 DELUXE ROOM
─────────────────────────────────────────────────────────
✓ Superficie: 30m²
✓ Cama: 1 king size
✓ Vista: Jardín o Piscina
✓ Capacidad: 2 personas
✓ Servicios incluidos:
  • Todo lo de Standard Room
  • TV LCD 42"
  • Cafetera Nespresso
  • Balcón privado
  • Bata y pantuflas
  • Amenities premium
  • Late checkout (14:00h)

💰 TARIFA: $120/noche
   (Temporada baja: $95/noche)

═══════════════════════════════════════════════════════════

🏨 JUNIOR SUITE
─────────────────────────────────────────────────────────
✓ Superficie: 45m²
✓ Cama: 1 king size + sofá cama
✓ Vista: Mar (parcial)
✓ Capacidad: 3 personas
✓ Servicios incluidos:
  • Todo lo de Deluxe Room
  • Sala de estar separada
  • TV LCD 55"
  • Minibar premium incluido
  • Bañera hidromasaje
  • Acceso a Lounge Ejecutivo
  • Welcome drink

💰 TARIFA: $180/noche
   (Temporada baja: $140/noche)

═══════════════════════════════════════════════════════════

🏨 PRESIDENTIAL SUITE
─────────────────────────────────────────────────────────
✓ Superficie: 80m²
✓ Habitaciones: 2 dormitorios + sala + comedor
✓ Camas: 2 king size
✓ Vista: Mar panorámica
✓ Capacidad: 6 personas
✓ Servicios incluidos:
  • TODO lo anterior
  • Cocina equipada
  • 3 TV (sala + 2 dormitorios)
  • Jacuzzi en terraza privada
  • Servicio de mayordomo 24h
  • Transfers aeropuerto incluidos
  • Champagne de bienvenida
  • Spa: 2 masajes de 60min incluidos

💰 TARIFA: $450/noche
   (Temporada baja: $350/noche)

═══════════════════════════════════════════════════════════
NOTAS:
• Check-in: 15:00h | Check-out: 12:00h
• Parking gratuito para huéspedes
• Mascotas: Permitidas (+$20/noche)
• Cuna infantil: Gratuita (bajo solicitud)
═══════════════════════════════════════════════════════════
```

### 💬 Conversaciones

```
👤 "¿Qué tipos de habitaciones tienen?"
🤖 [Responde con lista completa] 🏨

👤 "Cuál es la diferencia entre Standard y Deluxe"
🤖 [Compara: superficie, vista, servicios] 📋

👤 "Necesito una habitación para familia con 2 niños"
🤖 "Les recomiendo la Junior Suite (capacidad 3) + cuna gratuita,
     o la Presidential Suite si necesitan más espacio..." 👨‍👩‍👧‍👦
```

---

## Ejemplo 4: Spa con Servicios y Tratamientos

### 📄 Documento: `menu_tratamientos_spa.pdf`

```
═══════════════════════════════════════════════════════════
                    ZEN SPA
          MENÚ DE TRATAMIENTOS Y SERVICIOS
═══════════════════════════════════════════════════════════

💆 MASAJES
─────────────────────────────────────────────────────────

💆‍♀️ Masaje Relajante Sueco
   Duración: 60 min | $80
   Duración: 90 min | $110
   • Técnica de masaje clásico
   • Ideal para aliviar tensiones
   • Aceites aromáticos incluidos

💆‍♀️ Masaje de Tejido Profundo
   Duración: 60 min | $95
   Duración: 90 min | $130
   • Trabaja capas musculares profundas
   • Ideal para atletas
   • Alivia dolores crónicos

💆‍♀️ Masaje con Piedras Calientes
   Duración: 90 min | $140
   • Combina calor y presión
   • Mejora circulación
   • Profunda relajación

💆‍♀️ Masaje Tailandés
   Duración: 90 min | $120
   • Estiramientos asistidos
   • Mejora flexibilidad
   • Energizante

═══════════════════════════════════════════════════════════

🧖 TRATAMIENTOS FACIALES
─────────────────────────────────────────────────────────

🧖‍♀️ Facial Hidratante Premium
   Duración: 75 min | $110
   • Limpieza profunda
   • Mascarilla hidratante
   • Masaje facial + cuello

🧖‍♀️ Facial Anti-Edad Gold
   Duración: 90 min | $180
   • Productos con oro 24k
   • Radiofrecuencia
   • Serum anti-edad

🧖‍♀️ Facial Detox Carbón
   Duración: 60 min | $95
   • Limpieza profunda poros
   • Mascarilla carbón activado
   • Piel purificada

═══════════════════════════════════════════════════════════

💅 TRATAMIENTOS CORPORALES
─────────────────────────────────────────────────────────

💅 Exfoliación Corporal + Envolvente
   Duración: 90 min | $130
   • Exfoliación con sales marinas
   • Envolvente de algas
   • Hidratación profunda

💅 Ritual Chocolate
   Duración: 120 min | $160
   • Exfoliación cacao
   • Envolvente chocolate
   • Masaje 30min

═══════════════════════════════════════════════════════════

🎁 PAQUETES ESPECIALES
─────────────────────────────────────────────────────────

🎁 Paquete Relajación Total (3h)
   • Masaje 90min
   • Facial 60min
   • Acceso a área húmeda
   💰 $220 (Ahorro $45)

🎁 Paquete Día de Spa (5h)
   • Masaje piedras calientes 90min
   • Facial Premium 75min
   • Exfoliación corporal 45min
   • Manicure + Pedicure
   • Almuerzo saludable incluido
   • Acceso ilimitado área húmeda
   💰 $380 (Ahorro $95)

🎁 Paquete Parejas Romance (3h)
   • Masaje en suite privada 90min (2 personas)
   • Champagne + fresas
   • Acceso jacuzzi privado
   💰 $320 (para 2 personas)

═══════════════════════════════════════════════════════════
ÁREA HÚMEDA INCLUYE:
• Sauna finlandés
• Baño turco
• Jacuzzi
• Piscina temperada
• Duchas de sensaciones
═══════════════════════════════════════════════════════════
```

### 💬 Conversaciones

```
👤 "¿Qué servicios ofrecen?"
🤖 [Lista completa de tratamientos] 📋

👤 "Quiero un masaje relajante"
🤖 "Tenemos Masaje Relajante Sueco:
     • 60min - $80
     • 90min - $110
     Incluye aceites aromáticos..." 💆

👤 "Paquetes para parejas"
🤖 "Paquete Parejas Romance (3h) - $320:
     • Masaje 90min en suite privada
     • Champagne + fresas
     • Jacuzzi privado
     ¿Te gustaría reservar?" 💑
```

---

## 🎯 Patrones de Detección

El sistema detecta automáticamente estas consultas:

| Consulta Usuario | Tipo Detectado | Emoji | FAQ Retornado |
|-----------------|----------------|-------|---------------|
| "¿Qué clases tienen?" | `clases` | 💪 | Horario completo |
| "Ver catálogo de productos" | `productos` | 🛍️ | Catálogo completo |
| "Tipos de habitaciones" | `habitaciones` | 🏨 | Lista habitaciones |
| "¿Qué tratamientos ofrecen?" | `servicios` | 📋 | Menú tratamientos |
| "Lista de precios" | `tarifas` | 💰 | Tarifas según tipo |
| "¿Qué tienen en el menú?" | `menú` | 🍽️ | Menú restaurante |

---

## 🔍 Verificación del Sistema

### Script de Test

```bash
cd c:\Users\nacho\Desktop\chatbot\chatbot\backend
python test_universal_system.py
```

**Salida esperada:**
```
🎉 ¡TODOS LOS TESTS PASARON!
📊 RESULTADOS: 26 pasaron, 0 fallaron de 26 tests
```

### Verificar FAQs Creados

```python
import sqlite3

conn = sqlite3.connect('chatbot/chatbot.db')
cursor = conn.cursor()

# Ver todos los FAQs de prioridad 100
cursor.execute("""
    SELECT b.name, f.question, f.category, f.priority 
    FROM faqs f
    JOIN businesses b ON f.business_id = b.id
    WHERE f.priority >= 100
    ORDER BY b.id, f.priority DESC
""")

for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} (categoría: {row[2]}, prioridad: {row[3]})")
```

### Monitoreo en Tiempo Real

```powershell
# Ver detecciones y bypass
Get-Content logs\chatbot.log -Wait | Select-String "🎯|✅|🔍"
```

---

## 📝 Tips para Crear Documentos Óptimos

### ✅ Buenas Prácticas

1. **Estructura clara:**
   - Usa títulos y separadores
   - Organiza en secciones
   - Mantén formato consistente

2. **Información completa:**
   - Incluye TODOS los items
   - No uses "etc." o "..."
   - Especifica precios, horarios, detalles

3. **Formato legible:**
   - Tablas simples
   - Listas con bullets
   - Espaciado adecuado

### ❌ Evitar

- Imágenes con texto (el sistema extrae texto)
- Estructuras muy complejas
- Referencias a otras páginas
- Información fragmentada

---

**Todos estos ejemplos están listos para usar con el sistema universal** ✅
