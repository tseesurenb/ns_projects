#!/bin/bash
# Setup Nginx as reverse proxy on port 80 -> uvicorn port 8000
# Port 80 is typically open on all servers

# Install nginx if not present
sudo apt-get install -y -qq nginx

# Create nginx config
sudo tee /etc/nginx/sites-available/ns_crm > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site, disable default
sudo ln -sf /etc/nginx/sites-available/ns_crm /etc/nginx/sites-enabled/ns_crm
sudo rm -f /etc/nginx/sites-enabled/default

# Open port 80 in iptables
sudo iptables -I INPUT 5 -p tcp --dport 80 -m state --state NEW -j ACCEPT

# Test and start nginx
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "============================================"
echo "  Nginx configured!"
echo "  Try: http://161.118.212.47"
echo "  Register: http://161.118.212.47/app/register.html"
echo "============================================"
