#!/bin/bash
# Fix ns_crm systemd service — PYTHONPATH issue
# Run on server: bash fix_service.sh

sudo tee /etc/systemd/system/ns_crm.service > /dev/null << 'EOF'
[Unit]
Description=ns_crm — NS Projects
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu
Environment=PATH=/home/ubuntu/ns_crm/venv/bin:/usr/bin
Environment=PYTHONPATH=/home/ubuntu
ExecStart=/home/ubuntu/ns_crm/venv/bin/uvicorn ns_crm.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart ns_crm
sleep 2
sudo systemctl status ns_crm
