#!/bin/bash
# =============================================================
# Multi-Tenant SaaS — Server Preparation Script
# Target: Ubuntu server at 161.118.212.47
# Run this FROM YOUR LOCAL MACHINE (not on the server)
#
# Usage:
#   ./prep_server.sh          # Deploy ns_crm (default, full CRM)
#   ./prep_server.sh ns_base  # Deploy ns_base (platform only)
#   ./prep_server.sh ns_crm   # Deploy ns_crm (CRM project)
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY="$SCRIPT_DIR/ns-server/stt-server.key"
SERVER="ubuntu@161.118.212.47"
PROJECT="${1:-ns_crm}"
REMOTE_DIR="/home/ubuntu/$PROJECT"

if [ ! -d "$SCRIPT_DIR/$PROJECT" ]; then
  echo "Error: Project '$PROJECT' not found."
  echo "Available: $(ls -d "$SCRIPT_DIR"/ns_*/)"
  exit 1
fi

chmod 600 "$KEY" 2>/dev/null

run_remote() {
  ssh -i "$KEY" -o StrictHostKeyChecking=no "$SERVER" "$1"
}

echo "============================================"
echo "  NS Projects — Server Deployment"
echo "  Project:  $PROJECT"
echo "  Server:   161.118.212.47"
echo "============================================"
echo ""

# ------ Step 1: Install system dependencies ------
echo "[1/6] Installing system packages..."
run_remote "sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql postgresql-contrib git > /dev/null 2>&1"
echo "  Done"

# ------ Step 2: Setup PostgreSQL ------
echo "[2/6] Configuring PostgreSQL..."
DB_NAME="${PROJECT//-/_}_db"
run_remote "sudo -u postgres psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='saasadmin'\" | grep -q 1 || sudo -u postgres psql -c \"CREATE USER saasadmin WITH PASSWORD 'ChangeMeInProduction123';\" && sudo -u postgres psql -tc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1 || sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME OWNER saasadmin;\""
echo "  Done (DB: $DB_NAME, User: saasadmin)"

# ------ Step 3: Upload project files ------
echo "[3/6] Uploading project files..."
cd "$SCRIPT_DIR/$PROJECT"
tar czf /tmp/ns-deploy.tar.gz \
  --exclude='devenv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='*.db' \
  --exclude='.git' \
  --exclude='node_modules' \
  .

run_remote "mkdir -p $REMOTE_DIR"
scp -i "$KEY" -o StrictHostKeyChecking=no /tmp/ns-deploy.tar.gz "$SERVER:$REMOTE_DIR/"
run_remote "cd $REMOTE_DIR && tar xzf ns-deploy.tar.gz && rm ns-deploy.tar.gz"
rm -f /tmp/ns-deploy.tar.gz
echo "  Done"

# ------ Step 4: Setup Python virtual env ------
echo "[4/6] Setting up Python environment..."
run_remote "cd $REMOTE_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt -q"
echo "  Done"

# ------ Step 5: Create production .env ------
echo "[5/6] Creating production .env..."
SECRET=$(openssl rand -hex 32)
run_remote "cat > $REMOTE_DIR/.env << ENVEOF
# Application
APP_NAME=\"$PROJECT\"
DEBUG=false
ENVIRONMENT=production

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://saasadmin:ChangeMeInProduction123@localhost:5432/$DB_NAME

# Authentication
SECRET_KEY=$SECRET

# AI / LLM
ANTHROPIC_API_KEY=

# CORS
CORS_ORIGINS=[\"https://yourdomain.com\"]
ENVEOF"
echo "  Done"

# ------ Step 6: Create systemd service ------
echo "[6/6] Setting up systemd service..."
run_remote "sudo tee /etc/systemd/system/$PROJECT.service > /dev/null << SVCEOF
[Unit]
Description=$PROJECT — NS Projects
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$REMOTE_DIR
Environment=PATH=$REMOTE_DIR/venv/bin:/usr/bin
Environment=PYTHONPATH=$REMOTE_DIR
ExecStart=$REMOTE_DIR/venv/bin/uvicorn ${PROJECT}.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable $PROJECT
sudo systemctl start $PROJECT"
echo "  Done"

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo ""
echo "  $PROJECT running at: http://161.118.212.47:8000"
echo "  Frontend:            http://161.118.212.47:8000/app/register.html"
echo "  API docs:            http://161.118.212.47:8000/docs"
echo ""
echo "  Commands:"
echo "    ./connect_ns 'sudo systemctl status $PROJECT'"
echo "    ./connect_ns 'sudo systemctl restart $PROJECT'"
echo "    ./connect_ns 'sudo journalctl -u $PROJECT -f'"
echo ""
echo "  Update on server ($REMOTE_DIR/.env):"
echo "    1. PostgreSQL password"
echo "    2. ANTHROPIC_API_KEY"
echo "    3. CORS_ORIGINS"
echo ""
