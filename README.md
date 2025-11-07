# Chatbot IA Local para Empresas

Bienvenido a la documentación corporativa de **Chatbot IA Local**, nuestra plataforma integral para empresas que quieren automatizar la atención al cliente con inteligencia artificial privada, segura y autosuficiente. Aquí encontrarás la visión, propuesta de valor, detalles técnicos del producto y todo lo necesario para implementarlo en tu organización.

---

## 🏢 Quiénes somos

Somos una empresa española especializada en asistentes conversacionales **on-premise**. Ayudamos a negocios que desean disfrutar de los beneficios de la IA generativa sin exponer datos sensibles a proveedores externos. La plataforma está pensada para:

- **Retail y hostelería** que buscan automatizar reservas, horarios y preguntas frecuentes.
- **Centros deportivos y de salud** que necesitan soporte 24/7 para altas, horarios y promociones.
- **Consultoras y franquicias** que requieren personalizar el tono del asistente por marca o sucursal.

Nuestros pilares:

1. **Privacidad total**: los modelos corren en tus propios servidores o en redes privadas.
2. **Coste controlado**: cero cuotas por tokens ni dependencia de APIs externas.
3. **Personalización profunda**: tono, mensajes de bienvenida, FAQ por negocio y memoria contextual.
4. **Tiempo de respuesta real**: latencias inferiores a 1 segundo con modelos optimizados GPU/CPU.

---

## 💡 Propuesta de valor

| Necesidad del cliente | Cómo lo resolvemos |
|-----------------------|--------------------|
| Automatizar atención en horarios pico | Chat multicanal (web, widget embebido) operativo 24/7 |
| Cumplir con RGPD y políticas internas | Infraestructura 100% local, logs auditables y control de API keys |
| Mantener branding y tono corporativo | Panel admin para configurar tono, mensajes y límites de temperatura |
| Escalar a varias marcas o sedes | Arquitectura multi-business con SQLite/SQLServer opcional |
| Integración rápida con sistemas existentes | API REST documentada y scripts listos en PowerShell/Node |

---

## 🧭 Visión del producto

1. **Asistente inteligente** entrenado con FAQs y contexto de conversaciones previas.
2. **Panel administrativo** para gestionar negocios, personalizar respuestas, cargar nuevos contenidos y analizar conversaciones.
3. **Widget omnicanal** listo para incrustar en webs externas o kioskos, con persistencia de sesión y soporte para dispositivos móviles.
4. **Scripts de despliegue** que facilitan la instalación en Windows (PowerShell) o Linux (bash).

---

## 🔩 Arquitectura de referencia

```
┌─────────────────────┐      ┌────────────────────────┐
│   Frontend estático │◄────►│ FastAPI Backend (LAN)   │
│  index.html / widget│      │  + Servicios IA (GPT4All│
└─────────────────────┘      └───────┬────────────────┘
                                      │
                           ┌──────────┴──────────┐
                           │  Motor LLM local    │
                           │ (Meta-Llama / GPT4All│
                           └──────────┬──────────┘
                                      │
                           ┌──────────┴──────────┐
                           │   Base de datos     │
                           │  SQLite / SQL       │
                           └─────────────────────┘
```

- **Backend**: FastAPI + SQLAlchemy, orquesta mensajes, memoria y FAQ.
- **Modelos IA**: GPT4All / llama.cpp (Meta Llama 3.1-8B Q4_K_M incluido).
- **Frontend**: HTML/CSS/JS estático con widget embebible.
- **Admin**: Panel responsive para gestionar negocios, FAQs y configuraciones.
- **Scripts**: `run_backend_fixed.ps1` automatiza creación de entorno, dependencias y arranque en Windows con autodetección de IP LAN.

---

## 📦 Componentes del repositorio

| Carpeta / Archivo | Descripción |
|-------------------|-------------|
| `backend/` | API FastAPI, lógica de negocio, orm y modelos IA locales. |
| `backend/main.py` | Punto de entrada del servidor, rutas `/chat`, `/businesses`, `/faqs`, `/admin.html`, `/`. |
| `backend/add_gym_faqs.py` | Scripts de carga para FAQs de gimnasios. |
| `frontend/index.html` | Landing page corporativa con demo en vivo. |
| `frontend/admin.html` | Panel de administración y personalización. |
| `frontend/demo.html` | Ejemplo standalone para kioskos o Iframe. |
| `run_backend_fixed.ps1` | Instalación y arranque integral en Windows. |
| `logs/` | Transcripciones y bitácoras de funcionamiento. |

---

## ⚙️ Requisitos mínimos

| Rol | CPU / GPU | RAM | Almacenamiento |
|-----|-----------|-----|----------------|
| Desarrollo local | CPU 4 cores | 8 GB | 8 GB libre para modelo y DB |
| Producción ligera | CPU 8 cores o GPU 4 GB | 16 GB | SSD 40 GB |
| Producción alta | GPU 8 GB (RTX 3060 o superior) | 32 GB | SSD 80 GB |


**Software**

- Windows 10/11 o Linux (Ubuntu 22.04+) con Python 3.11.
- Node.js 18+ si usas el flujo con Vite (opcional).
- PowerShell 5.1+ para el script de despliegue en Windows.

---

## 🚀 Puesta en marcha rápida

### Opción recomendada (Windows)

```powershell
cd .\chatbot
.\run_backend_fixed.ps1
.\run_backend_fixed.ps1 -LanMode
.\run_backend_fixed.ps1 -HostIp 192.168.1.50
```

El script crea/activa el entorno virtual, instala dependencias, lanza Uvicorn y, si quieres, Vite. También imprime URL directas al backend, admin y páginas estáticas.

### Instalación manual (Linux / macOS)

```bash
git clone https://github.com/NachoGR8-alt/chatbot.git
cd chatbot/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py --host 0.0.0.0 --port 8000
```

Para servir el frontend estático basta con dejar que FastAPI sirva `/static`. Si deseas desarrollo en caliente:

```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Cambios recientes importantes (backend)

1. Protección ante fuga de instrucciones (prompt leaking)
  - Capas de limpieza en `app/services/chatbot_service.py` para evitar que el modelo devuelva instrucciones internas al usuario.

2. Detección de consultas tipo "todas las normas" (`wants_all_rules`)
  - Patrones añadidos en `app/api/routes/chat.py` para reconocer frases como "dime las normas", "normas del gimnasio" y similares.
  - Al detectarse, se eleva el número máximo de FAQs en contexto y se usa un prompt específico que lista todas las normas de forma concisa.

3. Filtrado de FAQs por relevancia
  - Pre-filtrado por palabras clave y similitud para reducir ruido y evitar mezclas de respuestas.

4. Presupuesto dinámico de tokens de salida
  - Cálculo de `max_tokens` basado en `num_faqs_in_context` con márgenes y límites configurables para minimizar truncados.

5. Logging detallado
  - Trazas sobre detecciones, recuento de FAQs incluidas y parámetros de generación para facilitar el diagnóstico.

Resultado: respuestas más completas y seguras, especialmente cuando el usuario solicita listados largos (p. ej., todas las normas del gimnasio).

---

## 🧪 Datos demo y validación

1. **Semilla de negocio demo**
   ```powershell
   Invoke-WebRequest -Uri http://<host>:8000/seed-demo -Method POST
   ```
2. **Prueba de salud**
   ```powershell
   Invoke-WebRequest -Uri http://<host>:8000/health
   ```
3. **Conversación de prueba**
   ```bash
   curl -X POST http://<host>:8000/chat \
        -H "Content-Type: application/json" \
        -d '{"business_id":1,"session_id":"demo","message":"¿Tenéis menu vegano?"}'
   ```

---

## 🎛️ Operación diaria

- **Logs**: `logs/run_backend.log` y `logs/chatbot.log` mantienen eventos clave.
- **Sesiones**: cada conversación se persiste en SQLite. Por defecto el backend apunta a `../chatbot.db` (ubicado en la raíz de este proyecto `chatbot/`). Puedes migrarlo a Postgres/SQL Server actualizando `DATABASE_URL`.
- **Claves administrativas**: establece la variable de entorno `ADMIN_API_KEY` para proteger `/admin/*`.
- **Actualizaciones de modelos**: deja tu modelo `.gguf` en `backend/models/` y exporta la ruta en `CHATBOT_MODEL_NAME`.
- **Mantenimiento**: programa rotación de logs y backups de DB (tar/scheduled task).

---

## 🧰 Troubleshooting rápido

- Backend no encuentra la base de datos
  - Verifica que `chatbot/chatbot.db` exista y que la ruta efectiva desde `backend/` sea `../chatbot.db`.

- El modelo no carga
  - Coloca el archivo `.gguf` en `backend/models/` y define `CHATBOT_MODEL_NAME` si usas otra ruta/nombre.

- Respuestas con instrucciones visibles (prompt leak)
  - Asegúrate de tener la versión actualizada de `app/services/chatbot_service.py`. Revisa `logs/chatbot.log` para ver qué filtros se aplicaron.

- Respuestas truncadas con "..."
  - Aumenta el budget de tokens o revisa la estimación dinámica en el servicio. Modelos más grandes también reducen truncado.

---

## 🌐 Canales y productos

| Módulo | Qué ofrece | Público objetivo |
|--------|------------|------------------|
| **Landing corporativa** | Presenta tu chatbot, incluye demo y CTA | Equipo comercial, clientes finales |
| **Widget embebible** | Conversación en tiempo real dentro de webs externas | Marketing digital, webmasters |
| **Panel Admin** | Gestión de negocios, FAQs, configuraciones y analytics básicos | Operaciones, customer success |
| **API REST** | Integración con CRM, ERP, apps móviles o kioskos | Equipos de IT |

---

## 🔒 Seguridad y cumplimiento

- Despliegue en redes privadas; no se envía información a terceros.
- Control de acceso mediante API Key para endpoints administrativos.
- Logs auditables y exportables para procesos de compliance.
- Posibilidad de aislar la base de datos en servidores cifrados (columna `bot_response` soporta encriptado futuro).

---

## 🧭 Roadmap

1. **Analytics avanzado**: dashboards con preguntas frecuentes, satisfacción y horarios pico.
2. **Integraciones nativas**: WhatsApp Business, Telegram y un conector SMTP para tickets.
3. **Multi-idioma automático**: detección de idioma y FAQ multilingüe.
4. **Playbooks**: acciones prediseñadas (reservas, enviar catálogos, pagos).
5. **Exportación CRM**: conectores con HubSpot, Salesforce y Zoho.

---

## 📞 Contacto y soporte

- **Email**: hola@chatbot.ai
- **Teléfono**: +34 600 000 000
- **Dirección**: Barcelona, España (oficina central)
- **Soporte Técnico**: SLA empresarial disponible bajo contrato.

¿Necesitas acompañamiento en la implementación? Escríbenos y nuestro equipo de expertos te guiará desde la instalación hasta la puesta en producción.

---

## 📝 Licencia y contribuciones

Este proyecto se distribuye con una licencia comercial. Para colaboraciones, integraciones a medida o licencias OEM, contáctanos directamente.

---

## ✅ Checklist de lanzamiento rápido

1. [ ] Ejecutar `run_backend_fixed.ps1` y confirmar URLs impresas.
2. [ ] Sembrar datos demo (`/seed-demo`).
3. [ ] Configurar `ADMIN_API_KEY` y probar panel en `/admin.html`.
4. [ ] Personalizar `frontend/index.html` con branding propio.
5. [ ] Incrustar `widget.js` en la web corporativa.
6. [ ] Agendar backups de `chatbot.db`.

Con esto tendrás tu **Chatbot IA Local** funcionando, personalizable y alineado con las políticas de privacidad de tu empresa. ¡Bienvenido a la nueva generación de atención al cliente autónoma!

---

## 📞 SCRIPT DE VENTAS

### Email de Prospección

```
Asunto: ¿[Nombre Negocio] atiende clientes 24/7?

Hola [Nombre],

He visto [Nombre Negocio] y creo que podríais beneficiaros 
de un asistente virtual que responda automáticamente:

✅ "¿Qué horario tenéis?"
✅ "¿Tenéis menú sin gluten?"
✅ "Quiero hacer una reserva"

Ventajas:
• Respuestas instantáneas 24/7
• Sin costes de API mensuales
• Funciona en tu propio servidor
• Setup en menos de 1 hora

¿Te interesa una demo de 15 minutos?

[Tu nombre]
[Teléfono]
```

### Llamada de Seguimiento (Guión)

**1. Presentación (30 seg)**
> "Hola [Nombre], soy [Tu Nombre]. Te envié un email sobre 
> automatizar la atención al cliente de [Negocio]."

**2. Descubrir Dolor (1 min)**
> "¿Cuántas llamadas recibes diariamente preguntando horarios, 
> menú o precios? ¿Qué pasa cuando estás ocupado y no puedes atender?"

**3. Presentar Solución (2 min)**
> "Nuestro chatbot responde esas preguntas automáticamente, 
> 24/7, sin aumentar tu carga de trabajo. Y lo mejor: funciona 
> 100% en tu servidor, sin costes mensuales de APIs."

**4. Demo en Vivo (5 min)**
> [Compartir pantalla]
> "Mira, aquí está funcionando para un restaurante similar. 
> El cliente pregunta sobre el menú y recibe respuesta al instante..."

**5. Cierre (1 min)**
> "Podemos tenerlo funcionando en tu web esta misma semana. 
> ¿Empezamos con un trial de 14 días sin compromiso?"

**Objeciones Comunes:**

- **"Es muy caro"**
  > "Sin costes recurrentes. Solo pagas la instalación inicial."

- **"No soy técnico"**
  > "Nosotros nos encargamos de todo el setup. Tú solo agregas las FAQs."

- **"¿Y si da respuestas incorrectas?"**
  > "El bot solo responde basándose en las FAQs que tú configures. 
  > Si no sabe algo, deriva al teléfono o email."

---

## 📝 LICENCIA Y SOPORTE

Este proyecto es de código abierto para uso comercial.

**Soporte:**
- Documentación: Este README
- API Docs: http://127.0.0.1:8000/docs
- Modelos GPT4All: https://gpt4all.io

---

## ✅ CHECKLIST DE DEPLOYMENT

### Antes de vender a un cliente:

- [ ] Backend funcionando en servidor propio
- [ ] Base de datos creada y probada
- [ ] Al menos 10 FAQs configuradas
- [ ] Widget personalizado con colores del cliente
- [ ] Probado en móvil y desktop
- [ ] Historial de conversaciones accesible
- [ ] Backup de base de datos configurado

### Entrega al cliente:

- [ ] URL del widget (`widget.js`)
- [ ] Código HTML para embedear
- [ ] Acceso al panel de admin (si aplica)
- [ ] Documentación de uso
- [ ] 1 hora de capacitación

---

## 🚀 ¡ESTÁS LISTO!

1. **Crear datos demo:** http://127.0.0.1:8000/seed-demo
2. **Probar frontend:** http://localhost:3000
3. **Ver documentación:** http://127.0.0.1:8000/docs

**Siguiente paso:** Personaliza las FAQs para tu primer cliente 💪