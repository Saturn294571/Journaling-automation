#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/accounting-demo"
APP_USER="accountingdemo"
MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"
TIMEOUT="${OLLAMA_TIMEOUT_SECONDS:-180}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo bash deploy/setup-vm.sh"
  exit 1
fi

if [[ "$(pwd)" != "${APP_DIR}" ]]; then
  echo "This script expects the project to be located at ${APP_DIR}."
  echo "Current directory: $(pwd)"
  exit 1
fi

echo "[1/8] Installing system packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  nginx \
  python3 \
  python3-pip \
  python3-venv \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-kor

echo "[2/8] Creating service user"
if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --home "${APP_DIR}" --shell /usr/sbin/nologin "${APP_USER}"
fi

echo "[3/8] Preparing Python virtual environment"
python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/python" -m pip install -r "${APP_DIR}/requirements.txt"

echo "[4/8] Preparing app directories and environment"
mkdir -p "${APP_DIR}/uploads"
touch "${APP_DIR}/uploads/.gitkeep"
cat > "${APP_DIR}/.env" <<EOF
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=${MODEL}
OLLAMA_TIMEOUT_SECONDS=${TIMEOUT}
EOF
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "[5/8] Installing Ollama if needed"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
systemctl enable --now ollama

echo "[6/8] Pulling Ollama model: ${MODEL}"
sudo -u ollama ollama pull "${MODEL}" || ollama pull "${MODEL}"

echo "[7/8] Installing systemd and nginx configuration"
cp "${APP_DIR}/deploy/accounting-demo.service" /etc/systemd/system/accounting-demo.service
cp "${APP_DIR}/deploy/nginx-accounting-demo.conf" /etc/nginx/sites-available/accounting-demo
ln -sfn /etc/nginx/sites-available/accounting-demo /etc/nginx/sites-enabled/accounting-demo
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo "[8/8] Starting services"
systemctl daemon-reload
systemctl enable --now accounting-demo
systemctl restart nginx

echo
echo "Deployment finished."
echo "Check app service: sudo systemctl status accounting-demo --no-pager"
echo "Check app logs:    sudo journalctl -u accounting-demo -f"
echo "Check Ollama logs: sudo journalctl -u ollama -f"
