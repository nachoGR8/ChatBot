#!/usr/bin/env bash
# Prepara un VPS Ubuntu 24.04 recién creado y arranca el chatbot con HTTPS.
# Uso (como root, desde la carpeta deploy/ del repositorio):   bash setup.sh
# Se puede repetir sin problema: lo que ya está hecho se salta.
set -euo pipefail

cd "$(dirname "$0")"
MODEL_FILE="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/${MODEL_FILE}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

if [[ $EUID -ne 0 ]]; then
  echo "Ejecútalo como root:  sudo bash setup.sh" >&2
  exit 1
fi

log "1/6 Docker"
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  apt-get update -q
  apt-get install -y -q docker.io docker-compose-v2 curl openssl
  systemctl enable --now docker
else
  echo "Ya instalado: $(docker --version)"
fi

log "2/6 Swap de 2 GB (colchón de memoria para un VPS de 4 GB)"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -q vm.swappiness=10
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-chatbot.conf
else
  echo "Ya hay swap."
fi

log "3/6 Cortafuegos: solo SSH, HTTP y HTTPS"
if command -v ufw >/dev/null; then
  ufw allow OpenSSH >/dev/null
  ufw allow 80/tcp >/dev/null
  ufw allow 443 >/dev/null
  ufw --force enable >/dev/null
  ufw status | head -n 8
else
  echo "ufw no está instalado: usa el cortafuegos del panel de tu proveedor (abre 22, 80 y 443)."
fi

log "4/6 Modelo (${MODEL_FILE}, ~2 GB)"
mkdir -p models
if [[ -s "models/${MODEL_FILE}" ]]; then
  echo "Ya descargado."
else
  curl -fL --retry 3 -o "models/${MODEL_FILE}.part" "$MODEL_URL"
  mv "models/${MODEL_FILE}.part" "models/${MODEL_FILE}"
fi
# El contenedor corre con el usuario 1000: necesita poder leer el modelo.
chmod 755 models && chmod 644 models/*.gguf

log "5/6 Configuración (deploy/.env)"
[[ -f .env ]] || cp .env.example .env
if ! grep -q '^DOMAIN=..*' .env; then
  ip=$(curl -4 -fsS https://api.ipify.org)
  sed -i "s|^DOMAIN=.*|DOMAIN=${ip//./-}.sslip.io|" .env
  echo "Sin dominio propio: se usa ${ip//./-}.sslip.io (apunta a ${ip})."
fi
if ! grep -q '^ADMIN_API_KEY=..*' .env; then
  sed -i "s|^ADMIN_API_KEY=.*|ADMIN_API_KEY=$(openssl rand -hex 24)|" .env
  echo "Clave de administración generada."
fi
chmod 600 .env

log "6/6 Construir y arrancar (la 1.ª vez compila llama.cpp: 5-15 min)"
docker compose up -d --build

domain=$(grep '^DOMAIN=' .env | cut -d= -f2)
echo -n "Esperando a que cargue el modelo"
for _ in $(seq 1 90); do
  if curl -fsS "https://${domain}/health" >/dev/null 2>&1; then
    echo " listo."
    break
  fi
  echo -n "."
  sleep 5
done

cat <<EOF

Listo (si arriba no pone "listo", mira los logs: docker compose logs -f chatbot).

  Demo:   https://${domain}/demo.html
  Panel:  https://${domain}/admin.html
  Clave:  grep ADMIN_API_KEY $(pwd)/.env

Siguiente paso: entra al panel, crea tu negocio, sube tu CV y prueba la demo con ?business=ID.
EOF
