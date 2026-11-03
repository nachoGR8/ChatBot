# Desplegar en un VPS

Demo pública con HTTPS en un VPS barato: Caddy delante (certificado automático) y el chatbot con un modelo de 3B.

```
Internet ──443──▶ Caddy (HTTPS, cabeceras de seguridad) ──▶ chatbot:8000 (sin puerto público)
                                                              ├─ Llama 3.2 3B Q4_K_M (volumen ./models)
                                                              └─ SQLite + documentos (volúmenes Docker)
```

## Qué VPS

| | Mínimo |
|---|---|
| CPU | 2 vCPU (x86_64 o ARM) |
| RAM | 4 GB (el modelo ocupa ~2,5 GB; el script añade 2 GB de swap) |
| Disco | 20 GB |
| Sistema | Ubuntu 24.04 |

El de 8B necesita ~6 GB de RAM y es unas 2,5 veces más lento: para un VPS barato, mejor el de 3B.
Más vCPU = respuestas más rápidas (lo que más tarda en CPU es leer el prompt).

## Instalación (10-20 minutos, casi todo esperando)

1. Crea el VPS con Ubuntu 24.04 y tu clave SSH. Entra: `ssh root@IP_DEL_VPS`
2. Descarga el proyecto y lanza el script:

   ```bash
   apt-get update && apt-get install -y git
   git clone https://github.com/nachoGR8/ChatBot.git
   cd ChatBot/deploy
   bash setup.sh
   ```

   El script instala Docker, añade swap, abre solo los puertos 22/80/443, descarga el modelo (~2 GB),
   crea `deploy/.env` con una clave de administración aleatoria y arranca todo.
   La primera vez compila llama.cpp para tu CPU (5-15 min).

3. Al terminar muestra las URLs. Sin dominio propio se usa `IP-CON-GUIONES.sslip.io`, que apunta a tu IP y
   tiene certificado HTTPS válido. Con dominio propio: crea un registro A hacia la IP, pon `DOMAIN=tudominio.com`
   en `deploy/.env` y ejecuta `docker compose up -d`.

4. Entra en `https://TU_DOMINIO/admin.html` con la clave (`grep ADMIN_API_KEY .env`), crea tu negocio,
   sube tu CV y prueba `https://TU_DOMINIO/demo.html?business=ID`.

## Incrustarlo en otra web (p. ej. el portfolio)

```html
<script>window.CHATBOT_BUSINESS_ID = 1;</script>
<script src="https://TU_DOMINIO/widget.js" defer></script>
```

La web tiene que estar en `CHATBOT_CORS_ORIGINS` (en `deploy/.env`, separadas por comas). Tras cambiar `.env`: `docker compose up -d`.

## Mantenimiento

| Tarea | Comando (en `deploy/`) |
|---|---|
| Ver logs | `docker compose logs -f chatbot` |
| Estado | `docker compose ps` (columna STATUS: `healthy`) |
| Actualizar a lo último de main | `bash update.sh` |
| Copia de la base de datos | `bash backup.sh` (guarda las 14 últimas en `deploy/backups/`) |
| Reiniciar | `docker compose restart chatbot` |
| Parar | `docker compose down` (los datos se conservan en los volúmenes) |

Para copias automáticas diarias: `crontab -e` y añade `0 4 * * * cd /root/ChatBot/deploy && bash backup.sh`.

## Seguridad en la demo pública

- El backend no publica puerto: solo Caddy lo alcanza, así la IP de `X-Forwarded-For` es fiable para el límite por IP.
- `CHATBOT_RATE_LIMIT_PER_MIN=10` por IP y mensajes de 1000 caracteres como mucho.
- La administración exige la clave; sin `ADMIN_API_KEY` queda deshabilitada.
- Entra al VPS solo con clave SSH (desactiva la contraseña en `/etc/ssh/sshd_config`: `PasswordAuthentication no`).

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| No hay HTTPS / error de certificado | Los puertos 80 y 443 deben estar abiertos también en el cortafuegos del proveedor. `docker compose logs caddy` |
| `Illegal instruction` al arrancar | La imagen se construyó en otra CPU. Reconstruye en el VPS, o con `--build-arg LLAMA_CMAKE_ARGS="-DGGML_NATIVE=OFF"` |
| El contenedor se reinicia solo | Falta memoria: `docker compose logs chatbot`, `free -h`. Usa el modelo de 3B y no bajes la swap |
| Respuestas cortadas por tiempo | Sube `CHATBOT_GENERATE_TIMEOUT` en `.env` o baja `CHATBOT_MAX_FAQS` |
| El widget no carga en tu web | Añade su origen exacto (con `https://`) a `CHATBOT_CORS_ORIGINS` |
