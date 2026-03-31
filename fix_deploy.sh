#!/bin/bash
# Fix deployment to use git repo directly instead of separate copy
# This way "git pull" always updates the running app

# Remove old separate copy
rm -rf ~/ns_crm

# Update systemd to point to git repo
sudo tee /etc/systemd/system/ns_crm.service > /dev/null << 'EOF'
[Unit]
Description=ns_crm — NS Projects
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/ns_projects
Environment=PATH=/home/ubuntu/ns_projects/ns_crm/venv/bin:/usr/bin
Environment=PYTHONPATH=/home/ubuntu/ns_projects
ExecStart=/home/ubuntu/ns_projects/ns_crm/venv/bin/uvicorn ns_crm.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Setup venv inside git repo if not exists
cd ~/ns_projects/ns_crm
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
else
    echo "venv already exists"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    SECRET=$(openssl rand -hex 32)
    cat > .env << ENVEOF
APP_NAME="ns_crm"
DEBUG=false
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://saasadmin:ChangeMeInProduction123@localhost:5432/ns_crm_db
SECRET_KEY=$SECRET
ANTHROPIC_API_KEY=
CORS_ORIGINS=["*"]
ENVEOF
fi

sudo systemctl daemon-reload
sudo systemctl restart ns_crm
sleep 2
sudo systemctl status ns_crm --no-pager

echo ""
echo "Done! Now 'git pull' will always update the running app."
echo "After git pull, just run: sudo systemctl restart ns_crm"
