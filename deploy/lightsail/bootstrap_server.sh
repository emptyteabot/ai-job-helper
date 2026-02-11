#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] apt update + base packages"
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx git curl

echo "[2/4] ensure nginx enabled"
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "[3/4] create app directory"
sudo mkdir -p /opt/ai-job-helper
sudo chown -R "$USER":"$USER" /opt/ai-job-helper

echo "[4/4] done"
echo "Next:"
echo "  1) copy project to /opt/ai-job-helper"
echo "  2) configure /opt/ai-job-helper/.env"
echo "  3) install venv deps + systemd + nginx conf"

