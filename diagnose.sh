#!/bin/bash
# Diagnose ns_crm connectivity issues

echo "=== 1. Service status ==="
sudo systemctl is-active ns_crm

echo ""
echo "=== 2. Port listening ==="
sudo ss -tlnp | grep 8000

echo ""
echo "=== 3. Local test ==="
curl -s --max-time 5 http://localhost:8000/api/v1/health

echo ""
echo ""
echo "=== 4. Opening port 8000 in iptables ==="
sudo iptables -I INPUT 5 -p tcp --dport 8000 -m state --state NEW -j ACCEPT
echo "Done"

echo ""
echo "=== 5. Verify iptables rule added ==="
sudo iptables -L INPUT -n | grep 8000

echo ""
echo "=== 6. Also open port 80 (for future nginx) ==="
sudo iptables -I INPUT 5 -p tcp --dport 80 -m state --state NEW -j ACCEPT

echo ""
echo "============================================"
echo "  iptables updated!"
echo ""
echo "  IMPORTANT: You also need to open port 8000"
echo "  in Oracle Cloud Console:"
echo "  Networking > VCN > Security Lists > Ingress Rules"
echo "  Source: 0.0.0.0/0 | Protocol: TCP | Port: 8000"
echo "============================================"
