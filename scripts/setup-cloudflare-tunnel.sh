#!/bin/bash

# RadioX Backend - Cloudflare Tunnel Setup
# Macht die API über api.radiox.cloud von außen erreichbar

set -e

echo "🚀 RadioX Backend - Cloudflare Tunnel Setup"
echo "============================================"
echo ""
echo "📋 Prerequisites Check:"
echo "- Cloudflare Account ✅"
echo "- Domain radiox.cloud bei Cloudflare ✅"  
echo "- Nameservers geändert ✅"
echo "- Zero Trust aktiviert ✅"
echo ""
echo "ℹ️  Falls noch nicht erledigt: docs/deployment/cloudflare-setup.md"
echo ""

# 1. Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📥 Installing cloudflared..."
    
    # Install für Linux/macOS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
        chmod +x cloudflared-linux-amd64
        sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install cloudflared
    fi
    
    echo "✅ cloudflared installed"
else
    echo "✅ cloudflared already installed"
fi

# 2. Check if authenticated
echo "🔐 Checking Cloudflare authentication..."
if ! cloudflared tunnel list &> /dev/null; then
    echo "❌ Not authenticated with Cloudflare!"
    echo "   Run: cloudflared tunnel login"
    echo "   See: docs/deployment/cloudflare-setup.md"
    exit 1
fi
echo "✅ Cloudflare authentication OK"

# 3. Check if tunnel exists
TUNNEL_NAME="radiox-backend"
echo "🔍 Checking for existing tunnel: $TUNNEL_NAME"

if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "✅ Tunnel '$TUNNEL_NAME' already exists"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
else
    echo "🆕 Creating new tunnel: $TUNNEL_NAME"
    cloudflared tunnel create $TUNNEL_NAME
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo "✅ Tunnel created with ID: $TUNNEL_ID"
fi

# 3. Create tunnel configuration
echo "📝 Creating tunnel configuration..."
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: /home/$(whoami)/.cloudflared/$TUNNEL_ID.json

ingress:
  # API Subdomain für Backend
  - hostname: api.radiox.cloud
    service: http://localhost:8000
    
  # Health Check Endpoint
  - hostname: api.radiox.cloud
    path: /health
    service: http://localhost:8000/health
    
  # Catch-all rule (required)
  - service: http_status:404

EOF

echo "✅ Tunnel configuration created"

# 4. Create DNS record
SUBDOMAIN="${RADIOX_SUBDOMAIN:-api}"
FULL_DOMAIN="$SUBDOMAIN.radiox.cloud"
echo "🌐 Creating DNS record for $FULL_DOMAIN..."
cloudflared tunnel route dns $TUNNEL_NAME $FULL_DOMAIN

echo "✅ DNS record created"

# 5. Get tunnel token for Docker
echo "🔑 Getting tunnel token for Docker..."
TUNNEL_TOKEN=$(cloudflared tunnel token $TUNNEL_NAME)

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo "1. Add this to your .env file:"
echo "   CLOUDFLARE_TUNNEL_TOKEN=$TUNNEL_TOKEN"
echo ""
echo "2. Deploy to your Proxmox LXC:"
echo "   scp -r . user@your-lxc-ip:/opt/radiox-backend/"
echo "   ssh user@your-lxc-ip"
echo "   cd /opt/radiox-backend"
echo "   docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "3. Your API will be available at:"
echo "   https://api.radiox.cloud"
echo ""
echo "🔒 Security: Alle Services nur über Cloudflare erreichbar - keine offenen Ports!" 