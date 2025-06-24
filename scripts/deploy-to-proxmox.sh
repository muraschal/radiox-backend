#!/bin/bash

# RadioX Backend - Proxmox LXC Deployment
# Deployt die Production-Version auf das Proxmox LXC

set -e

# Configuration
LXC_IP="${LXC_IP:-}"
LXC_USER="${LXC_USER:-root}"
DEPLOY_PATH="/opt/radiox-backend"

echo "🚀 RadioX Backend - Proxmox LXC Deployment"
echo "=========================================="

# 1. Check configuration
if [ -z "$LXC_IP" ]; then
    echo "❌ Error: LXC_IP environment variable not set"
    echo "   Usage: LXC_IP=192.168.1.100 ./scripts/deploy-to-proxmox.sh"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Create .env file with all required environment variables"
    exit 1
fi

echo "🎯 Target: $LXC_USER@$LXC_IP:$DEPLOY_PATH"

# 2. Build all services locally first
echo "🔨 Building all services locally..."
docker-compose -f docker-compose.production.yml build

echo "✅ All services built successfully"

# 3. Create deployment package
echo "📦 Creating deployment package..."
tar --exclude='venv' \
    --exclude='logs' \
    --exclude='temp' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    -czf radiox-backend-deploy.tar.gz .

echo "✅ Deployment package created"

# 4. Upload to LXC
echo "📤 Uploading to LXC container..."
scp radiox-backend-deploy.tar.gz $LXC_USER@$LXC_IP:/tmp/

# 5. Deploy on LXC
echo "🚀 Deploying on LXC container..."
ssh $LXC_USER@$LXC_IP << 'EOF'
    # Stop existing services
    if [ -d "/opt/radiox-backend" ]; then
        cd /opt/radiox-backend
        docker-compose -f docker-compose.production.yml down || true
    fi
    
    # Create deploy directory
    mkdir -p /opt/radiox-backend
    cd /opt/radiox-backend
    
    # Extract new version
    tar -xzf /tmp/radiox-backend-deploy.tar.gz
    
    # Ensure directories exist
    mkdir -p logs temp outplay web jingles
    
    # Set permissions
    chown -R 1000:1000 logs temp outplay web
    
    # Start services
    docker-compose -f docker-compose.production.yml up -d
    
    # Check health
    sleep 10
    docker-compose -f docker-compose.production.yml ps
    
    # Cleanup
    rm /tmp/radiox-backend-deploy.tar.gz
    
    echo "✅ Deployment complete!"
    echo "🌐 API available at: https://api.radiox.cloud"
    echo "📊 Health check: https://api.radiox.cloud/health"
EOF

# 6. Cleanup local package
rm radiox-backend-deploy.tar.gz

# 7. Test deployment
echo "🧪 Testing deployment..."
sleep 5

if curl -f -s https://api.radiox.cloud/health > /dev/null; then
    echo "✅ Deployment successful! API is responding"
    echo "🌐 Your RadioX Backend is live at: https://api.radiox.cloud"
else
    echo "⚠️  Deployment completed but health check failed"
    echo "   Check logs: ssh $LXC_USER@$LXC_IP 'cd $DEPLOY_PATH && docker-compose logs'"
fi

echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "📍 LXC Container: $LXC_IP"
echo "🌐 Public API: https://api.radiox.cloud"
echo "🏥 Health Check: https://api.radiox.cloud/health"
echo "📋 Frontend Update: Update radiox-frontend to use https://api.radiox.cloud"
echo ""
echo "🔧 Management Commands:"
echo "   ssh $LXC_USER@$LXC_IP 'cd $DEPLOY_PATH && docker-compose -f docker-compose.production.yml logs'"
echo "   ssh $LXC_USER@$LXC_IP 'cd $DEPLOY_PATH && docker-compose -f docker-compose.production.yml restart'" 