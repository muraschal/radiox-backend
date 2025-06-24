# RadioX Microservices Makefile
# Easy management and deployment of all services

.PHONY: help build up down logs clean test health status

# Default target
help:
	@echo "RadioX Microservices Management"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  build      - Build all Docker images"
	@echo "  up         - Start all services"
	@echo "  down       - Stop all services"
	@echo "  logs       - Show logs from all services"
	@echo "  clean      - Clean up containers and images"
	@echo "  test       - Run health checks on all services"
	@echo "  health     - Check health of all services"
	@echo "  status     - Show status of all services"
	@echo "  restart    - Restart all services"
	@echo ""
	@echo "Service-specific commands:"
	@echo "  build-api  - Build API Gateway"
	@echo "  build-show - Build Show Service"
	@echo "  logs-api   - Show API Gateway logs"
	@echo "  logs-show  - Show Show Service logs"

# Build all services
build:
	@echo "🔨 Building all microservices..."
	docker-compose build

# Build specific services
build-api:
	@echo "🔨 Building API Gateway..."
	docker-compose build api-gateway

build-show:
	@echo "🔨 Building Show Service..."
	docker-compose build show-service

build-content:
	@echo "🔨 Building Content Service..."
	docker-compose build content-service

build-data:
	@echo "🔨 Building Data Service..."
	docker-compose build data-service

# Start all services
up:
	@echo "🚀 Starting all microservices..."
	docker-compose up -d
	@echo "✅ All services started!"
	@echo "🌐 API Gateway: http://localhost:8000"
	@echo "📊 Services Status: http://localhost:8000/services/status"

# Start services with logs
up-logs:
	@echo "🚀 Starting all microservices with logs..."
	docker-compose up

# Stop all services
down:
	@echo "🛑 Stopping all microservices..."
	docker-compose down
	@echo "✅ All services stopped!"

# Show logs
logs:
	@echo "📋 Showing logs from all services..."
	docker-compose logs -f

# Service-specific logs
logs-api:
	docker-compose logs -f api-gateway

logs-show:
	docker-compose logs -f show-service

logs-content:
	docker-compose logs -f content-service

logs-data:
	docker-compose logs -f data-service

logs-redis:
	docker-compose logs -f redis

# Health checks
health:
	@echo "🏥 Checking health of all services..."
	@curl -s http://localhost:8000/health || echo "❌ API Gateway not responding"
	@curl -s http://localhost:8001/health || echo "❌ Show Service not responding"
	@curl -s http://localhost:8002/health || echo "❌ Content Service not responding"
	@curl -s http://localhost:8006/health || echo "❌ Data Service not responding"
	@echo "✅ Health check completed!"

# Service status
status:
	@echo "📊 Service Status:"
	@echo "=================="
	@curl -s http://localhost:8000/services/status | python3 -m json.tool || echo "❌ Cannot get service status"

# Restart services
restart: down up

# Clean up
clean:
	@echo "🧹 Cleaning up containers and images..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed!"

# Development setup
dev-setup:
	@echo "🛠️ Setting up development environment..."
	@echo "Creating .env file..."
	@if [ ! -f .env ]; then \
		echo "SUPABASE_URL=your_supabase_url" > .env; \
		echo "SUPABASE_KEY=your_supabase_key" >> .env; \
		echo "OPENAI_API_KEY=your_openai_key" >> .env; \
		echo "ELEVENLABS_API_KEY=your_elevenlabs_key" >> .env; \
		echo "📝 Please edit .env file with your API keys"; \
	fi

# Test show generation
test-show:
	@echo "🎵 Testing show generation..."
	@curl -X POST http://localhost:8000/api/v1/shows/generate \
		-H "Content-Type: application/json" \
		-d '{"preset_name": "zurich", "news_count": 2}' \
		| python3 -m json.tool

# Monitor services
monitor:
	@echo "📊 Monitoring services..."
	@watch -n 5 'curl -s http://localhost:8000/services/status | python3 -m json.tool'

# Show service URLs
urls:
	@echo "🌐 Service URLs:"
	@echo "================"
	@echo "API Gateway:      http://localhost:8000"
	@echo "Show Service:     http://localhost:8001"
	@echo "Content Service:  http://localhost:8002"
	@echo "Audio Service:    http://localhost:8003"
	@echo "Media Service:    http://localhost:8004"
	@echo "Speaker Service:  http://localhost:8005"
	@echo "Data Service:     http://localhost:8006"
	@echo "Analytics Service: http://localhost:8007"
	@echo ""
	@echo "📊 API Documentation:"
	@echo "API Gateway Docs: http://localhost:8000/docs"
	@echo "Services Status:  http://localhost:8000/services/status"

# Quick development workflow
dev: build up health urls 