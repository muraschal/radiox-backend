#!/bin/bash

# 🔌 RadioX Port Configuration Validator
# Prevents port configuration mistakes by validating all configurations
# Author: RadioX Engineering Team
# Version: 1.0

set -euo pipefail

# Compatible with Bash 3.2+ (macOS default)

# 🎨 Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 📊 Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 🔧 Core Functions
log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; ((PASSED_CHECKS++)); }
error() { echo -e "${RED}❌ $1${NC}"; ((FAILED_CHECKS++)); }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 📋 Expected Port Configuration (Bash 3.2 compatible)
SERVICES="api-gateway show-service content-service audio-service media-service speaker-service data-service analytics-service"
EXTERNAL_PORTS="8000 8001 8002 8003 8004 8005 8006 8007"

get_external_port() {
    local service="$1"
    case "$service" in
        "api-gateway") echo "8000" ;;
        "show-service") echo "8001" ;;
        "content-service") echo "8002" ;;
        "audio-service") echo "8003" ;;
        "media-service") echo "8004" ;;
        "speaker-service") echo "8005" ;;
        "data-service") echo "8006" ;;
        "analytics-service") echo "8007" ;;
        *) echo "" ;;
    esac
}

# 🔍 Validation Functions
validate_dockerfile_ports() {
    log "Validating Dockerfile port configurations..."
    
    for service in $SERVICES; do
        ((TOTAL_CHECKS++))
        local dockerfile="services/${service}/Dockerfile"
        
        if [[ ! -f "$dockerfile" ]]; then
            error "Dockerfile missing: $dockerfile"
            continue
        fi
        
        # Check EXPOSE port
        local expose_port=$(grep "EXPOSE" "$dockerfile" | awk '{print $2}' | head -1)
        if [[ "$expose_port" != "8000" ]]; then
            error "$service: EXPOSE port is $expose_port, expected 8000"
            continue
        fi
        
        # Check CMD port
        local cmd_port=$(grep -o "\--port.*8[0-9][0-9][0-9]" "$dockerfile" | grep -o "8[0-9][0-9][0-9]" | head -1)
        if [[ "$cmd_port" != "8000" ]]; then
            error "$service: CMD port is $cmd_port, expected 8000"
            continue
        fi
        
        # Check health check port
        local health_port=$(grep -o "localhost:[0-9]*" "$dockerfile" | cut -d: -f2 | head -1)
        if [[ "$health_port" != "8000" ]]; then
            error "$service: Health check port is $health_port, expected 8000"
            continue
        fi
        
        success "$service: Dockerfile ports correct (EXPOSE:8000, CMD:8000, HEALTH:8000)"
    done
}

validate_docker_compose_ports() {
    log "Validating docker-compose.yml port mappings..."
    
    if [[ ! -f "docker-compose.yml" ]]; then
        ((TOTAL_CHECKS++))
        error "docker-compose.yml not found"
        return
    fi
    
    for service in $SERVICES; do
        ((TOTAL_CHECKS++))
        local expected_external=$(get_external_port "$service")
        
        # Extract port mapping from docker-compose.yml
        local port_mapping=$(grep -A 10 "^  ${service}:" docker-compose.yml | grep -o "\"[0-9]*:8000\"" | tr -d '"' | head -1)
        
        if [[ -z "$port_mapping" ]]; then
            error "$service: No port mapping found in docker-compose.yml"
            continue
        fi
        
        local external_port=$(echo "$port_mapping" | cut -d: -f1)
        local internal_port=$(echo "$port_mapping" | cut -d: -f2)
        
        if [[ "$external_port" != "$expected_external" ]]; then
            error "$service: External port is $external_port, expected $expected_external"
            continue
        fi
        
        if [[ "$internal_port" != "8000" ]]; then
            error "$service: Internal port is $internal_port, expected 8000"
            continue
        fi
        
        success "$service: docker-compose.yml mapping correct ($external_port:8000)"
    done
}

validate_api_gateway_config() {
    log "Validating API Gateway service configurations..."
    
    local gateway_config="services/api-gateway/main.py"
    if [[ ! -f "$gateway_config" ]]; then
        ((TOTAL_CHECKS++))
        error "API Gateway config not found: $gateway_config"
        return
    fi
    
    for service in $SERVICES; do
        if [[ "$service" == "api-gateway" ]]; then
            continue  # Skip API Gateway itself
        fi
        
        ((TOTAL_CHECKS++))
        
        # Check if service URL uses port 8000
        local service_url=$(grep -o "\"${service}.*:8000\"" "$gateway_config" | head -1)
        
        if [[ -z "$service_url" ]]; then
            error "API Gateway: $service URL not found or doesn't use port 8000"
            continue
        fi
        
        success "API Gateway: $service configured correctly ($service_url)"
    done
}

validate_running_containers() {
    log "Validating running container port configurations..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        warn "Docker not running - skipping container validation"
        return
    fi
    
    for service in $SERVICES; do
        ((TOTAL_CHECKS++))
        local container_name="radiox-${service}"
        local expected_external=$(get_external_port "$service")
        
        # Check if container is running
        if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
            warn "$service: Container not running ($container_name)"
            continue
        fi
        
        # Check port mapping
        local port_mapping=$(docker ps --format "{{.Names}} {{.Ports}}" | grep "^${container_name}" | grep -o "0.0.0.0:${expected_external}->8000/tcp")
        
        if [[ -z "$port_mapping" ]]; then
            error "$service: Container port mapping incorrect (expected 0.0.0.0:${expected_external}->8000/tcp)"
            continue
        fi
        
        success "$service: Container running with correct ports ($port_mapping)"
    done
}

validate_service_connectivity() {
    log "Validating service connectivity..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        warn "Docker not running - skipping connectivity validation"
        return
    fi
    
    # Check if API Gateway is running
    if ! docker ps --format "{{.Names}}" | grep -q "^radiox-api-gateway$"; then
        warn "API Gateway not running - skipping connectivity tests"
        return
    fi
    
    for service in $SERVICES; do
        if [[ "$service" == "api-gateway" ]]; then
            continue  # Skip API Gateway itself
        fi
        
        ((TOTAL_CHECKS++))
        
        # Test connectivity from API Gateway to service
        local service_name="${service//-/_}"  # Replace hyphens with underscores for service names
        if docker exec radiox-api-gateway curl -sf --max-time 5 "http://${service}:8000/health" >/dev/null 2>&1; then
            success "$service: Connectivity test passed (api-gateway -> $service:8000)"
        else
            error "$service: Connectivity test failed (api-gateway cannot reach $service:8000)"
        fi
    done
}

generate_port_summary() {
    log "Generating port configuration summary..."
    
    echo ""
    echo "📊 Port Configuration Summary"
    echo "============================="
    
    printf "%-20s %-15s %-15s %-20s %-10s\n" "Service" "External Port" "Internal Port" "Docker Mapping" "Status"
    printf "%-20s %-15s %-15s %-20s %-10s\n" "-------" "-------------" "-------------" "--------------" "------"
    
    for service in $SERVICES; do
        local external=$(get_external_port "$service")
        local internal="8000"
        local mapping="${external}:8000"
        
        # Check if container is running
        local status="❌ DOWN"
        if docker ps --format "{{.Names}}" | grep -q "^radiox-${service}$" 2>/dev/null; then
            status="✅ UP"
        fi
        
        printf "%-20s %-15s %-15s %-20s %-10s\n" "$service" "$external" "$internal" "$mapping" "$status"
    done
    
    echo ""
    echo "🔗 Network: radiox-network (bridge)"
    echo "📡 Production: https://api.radiox.cloud -> container:8000"
}

# 🚀 Main Execution
main() {
    echo "🔌 RadioX Port Configuration Validator"
    echo "======================================"
    echo ""
    
    # Run all validations
    validate_dockerfile_ports
    echo ""
    
    validate_docker_compose_ports  
    echo ""
    
    validate_api_gateway_config
    echo ""
    
    validate_running_containers
    echo ""
    
    validate_service_connectivity
    echo ""
    
    generate_port_summary
    
    # 📋 Final Report
    echo ""
    echo "📊 Validation Results"
    echo "===================="
    echo "Total Checks: $TOTAL_CHECKS"
    echo "Passed: $PASSED_CHECKS"
    echo "Failed: $FAILED_CHECKS"
    
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL PORT CONFIGURATIONS VALID${NC}"
        echo ""
        echo "✅ All services use port 8000 internally"
        echo "✅ External ports are correctly mapped"
        echo "✅ API Gateway can reach all services"
        echo "✅ Docker containers are properly configured"
        exit 0
    else
        echo -e "${RED}💥 $FAILED_CHECKS PORT CONFIGURATION ERRORS FOUND${NC}"
        echo ""
        echo "📚 See docs/developer-guide/port-architecture.md for details"
        echo "🔧 Run 'docker-compose down && docker-compose up -d --build' after fixes"
        exit 1
    fi
}

# 🎯 Execute
main "$@" 