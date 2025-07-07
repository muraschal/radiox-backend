#!/bin/bash

# 🚀 RadioX Ultimate Deployment Script - UNICORN EDITION
# =====================================================
# 
# Google Engineering Level Deployment with:
# - Optimized Docker Images
# - Database Factory Performance
# - HTTP Client Factory Networking
# - Centralized Configuration Management
# 
# Author: Marcel & Claude - Building the Next Unicorn 🦄

set -e

echo "🦄 RADIOX ULTIMATE DEPLOYMENT STARTING..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_unicorn() {
    echo -e "${PURPLE}[UNICORN]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found! Please create it with your configuration."
    exit 1
fi

print_success ".env file found"

# Load environment variables
source .env

# Validate required environment variables
required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_success "Environment variables validated"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs temp outplay
print_success "Directories created"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans || true
print_success "Existing containers stopped"

# Clean up old images (optional)
if [ "$1" = "--clean" ]; then
    print_status "Cleaning up old Docker images..."
    docker system prune -f
    docker image prune -f
    print_success "Docker cleanup completed"
fi

# Build base images first (for caching)
print_status "Building ultimate base images..."
print_unicorn "🏗️ Building service-base image..."
docker build -f Dockerfile.base --target service-base -t radiox-service-base:latest .

print_unicorn "🎵 Building audio-service-base image..."
docker build -f Dockerfile.base --target audio-service-base -t radiox-audio-base:latest .

print_success "Base images built successfully"

# Build and start all services
print_status "Building and starting all services..."
docker-compose up --build -d

print_success "All services started"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Health check all services
print_status "Performing health checks..."

services=(
    "api-gateway:8000"
)

all_healthy=true

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    print_status "Checking $service_name..."
    
    # Try to connect to the service
    for i in {1..30}; do
        if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            break
        else
            if [ $i -eq 30 ]; then
                print_error "$service_name failed health check"
                all_healthy=false
            else
                sleep 2
            fi
        fi
    done
done

# Show service status
print_status "Service Status:"
docker-compose ps

# Show logs if any service is unhealthy
if [ "$all_healthy" = false ]; then
    print_warning "Some services are unhealthy. Showing logs..."
    docker-compose logs --tail=50
fi

# Performance check
print_status "Checking performance metrics..."
if curl -s http://localhost:8000/database/stats > /dev/null 2>&1; then
    print_unicorn "🚀 Database factory performance endpoint available"
fi

if curl -s http://localhost:8000/http/stats > /dev/null 2>&1; then
    print_unicorn "🌐 HTTP client factory performance endpoint available"
fi

# Final status
echo ""
print_unicorn "🦄 RADIOX ULTIMATE DEPLOYMENT COMPLETED!"
echo "=========================================="
echo ""
print_status "Services available at:"
echo "  🌐 API Gateway: http://localhost:8000"
echo "  📊 Health Check: http://localhost:8000/health"
echo "  🗄️ Database Stats: http://localhost:8000/database/stats"
echo "  🌐 HTTP Stats: http://localhost:8000/http/stats"
echo ""
print_status "Docker services:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

if [ "$all_healthy" = true ]; then
    print_unicorn "🎉 ALL SYSTEMS OPERATIONAL - UNICORN MODE ACTIVATED!"
    print_unicorn "🚀 Ready to generate professional radio shows!"
else
    print_warning "⚠️ Some services need attention. Check logs above."
fi

echo ""
print_status "Useful commands:"
echo "  📊 View logs: docker-compose logs -f"
echo "  🔄 Restart: docker-compose restart"
echo "  🛑 Stop: docker-compose down"
echo "  🧹 Clean rebuild: $0 --clean"
echo ""
print_unicorn "🦄 HAPPY RADIO GENERATION!" 