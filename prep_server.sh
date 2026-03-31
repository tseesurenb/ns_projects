#!/bin/bash
# =============================================================
# Multi-Tenant SaaS — Server Preparation Script
# Target: Ubuntu server at 161.118.212.47
# Run this FROM YOUR LOCAL MACHINE (not on the server)
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY="$SCRIPT_DIR/ns-server/stt-server.key"
SERVER="ubuntu@161.118.212.47"
APP_NAME="multitenant-saas"
REMOTE_DIR="/home/ubuntu/$APP_NAME"

chmod 600 "$KEY" 2>/dev/null

# Helper: run command on server
run_remote() {
  ssh -i "$KEY" -o StrictHostKeyChecking=no "$SERVER" "$1"
}

echo "============================================"
echo "  Multi-Tenant SaaS — Server Prep"
echo "  Server: 161.118.212.47"
echo "============================================"
echo ""

# ------ Step 1: Install system dependencies ------
echo "[1/6] Installing system packages..."
run_remote "sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql postgresql-contrib git > /dev/null 2>&1"
echo "  ✓ System packages installed"

# ------ Step 2: Setup PostgreSQL ------
echo "[2/6] Configuring PostgreSQL..."
run_remote "sudo -u postgres psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='saasadmin'\" | grep -q 1 || sudo -u postgres psql -c \"CREATE USER saasadmin WITH PASSWORD 'ChangeMeInProduction123';\" && sudo -u postgres psql -tc \"SELECT 1 FROM pg_database WHERE datname='multitenant_saas'\" | grep -q 1 || sudo -u postgres psql -c \"CREATE DATABASE multitenant_saas OWNER saasadmin;\""
echo "  ✓ PostgreSQL configured (DB: multitenant_saas, User: saasadmin)"

# ------ Step 3: Upload project files ------
echo "[3/6] Uploading project files..."
# Create temp archive excluding unnecessary files
cd "$SCRIPT_DIR"
tar czf /tmp/saas-deploy.tar.gz \
  --exclude='ns-server' \
  --exclude='devenv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='multitenant_saas.db' \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='prep_server.sh' \
  --exclude='connect_ns' \
  .

run_remote "mkdir -p $REMOTE_DIR"
scp -i "$KEY" -o StrictHostKeyChecking=no /tmp/saas-deploy.tar.gz "$SERVER:$REMOTE_DIR/"
run_remote "cd $REMOTE_DIR && tar xzf saas-deploy.tar.gz && rm saas-deploy.tar.gz"
rm -f /tmp/saas-deploy.tar.gz
echo "  ✓ Project files uploaded"

# ------ Step 4: Setup Python virtual env ------
echo "[4/6] Setting up Python environment..."
run_remote "cd $REMOTE_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt -q"
echo "  ✓ Python environment ready"

# ------ Step 5: Create production .env ------
echo "[5/6] Creating production .env..."
run_remote "cat > $REMOTE_DIR/.env << 'ENVEOF'
# Application
APP_NAME=\"Multi-Tenant SaaS Platform\"
DEBUG=false
ENVIRONMENT=production

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://saasadmin:ChangeMeInProduction123@localhost:5432/multitenant_saas

# Authentication — CHANGE THIS!
SECRET_KEY=$(openssl rand -hex 32)

# AI / LLM
ANTHROPIC_API_KEY=

# CORS — update with your domain
CORS_ORIGINS=[\"https://yourdomain.com\"]
ENVEOF"
echo "  ✓ Production .env created"

# ------ Step 6: Create systemd service ------
echo "[6/6] Setting up systemd service..."
run_remote "sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << 'SVCEOF'
[Unit]
Description=Multi-Tenant SaaS Platform
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/multitenant-saas
Environment=PATH=/home/ubuntu/multitenant-saas/venv/bin:/usr/bin
ExecStart=/home/ubuntu/multitenant-saas/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME"
echo "  ✓ Service configured and started"

echo ""
echo "============================================"
echo "  ✓ Deployment complete!"
echo "============================================"
echo ""
echo "  App running at: http://161.118.212.47:8000"
echo "  Frontend:       http://161.118.212.47:8000/app/register.html"
echo ""
echo "  Useful commands (via ./connect_ns):"
echo "    ./connect_ns 'sudo systemctl status $APP_NAME'   # Check status"
echo "    ./connect_ns 'sudo systemctl restart $APP_NAME'  # Restart"
echo "    ./connect_ns 'sudo journalctl -u $APP_NAME -f'   # View logs"
echo ""
echo "  IMPORTANT — update these on the server:"
echo "    1. PostgreSQL password in .env"
echo "    2. SECRET_KEY (already generated, but verify)"
echo "    3. ANTHROPIC_API_KEY if using AI features"
echo "    4. CORS_ORIGINS with your actual domain"
echo ""
