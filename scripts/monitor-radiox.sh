#!/bin/bash

# RadioX Live Monitoring Dashboard
# Marcel - Real-time monitoring for RadioX pipeline

echo "🎵 RadioX Live Monitoring Dashboard 🎵"
echo "======================================"
echo "Press Ctrl+C to exit"
echo ""

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to get service status
get_service_status() {
    local service=$1
    local port=$2
    
    # Check Docker health status first
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' radiox-$service 2>/dev/null)
    
    if [ "$health_status" = "healthy" ]; then
        echo -e "${GREEN}●${NC}"
    elif [ "$health_status" = "unhealthy" ]; then
        echo -e "${RED}●${NC}"
    else
        # Fallback to port check for services without health check
        if curl -s -m 2 "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${YELLOW}●${NC}"
        else
            echo -e "${RED}●${NC}"
        fi
    fi
}

# Function to get API stats
get_api_stats() {
    local stats=$(curl -s -m 3 "http://localhost:8000/api/v1/shows?limit=100" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$stats" ]; then
        local total=$(echo "$stats" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    shows = data.get('shows', [])
    print(len(shows))
except:
    print(0)
" 2>/dev/null || echo "0")
        echo "$total"
    else
        echo "?"
    fi
}

# Function to get latest show info
get_latest_show() {
    local show_data=$(curl -s -m 3 "http://localhost:8000/api/v1/shows?limit=1" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$show_data" ]; then
        echo "$show_data" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    shows = data.get('shows', [])
    if shows and len(shows) > 0:
        show = shows[0]
        title = show.get('title', 'Unknown')[:30]
        created = show.get('created_at', '')[:16]
        print(title + ' (' + created + ')')
    else:
        print('No shows available')
except Exception as e:
    print('Error parsing show data')
" 2>/dev/null || echo "Error getting show data"
    else
        echo "API unavailable"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo -e "${CYAN}🎵 RadioX Live Monitoring Dashboard 🎵${NC}"
    echo "======================================"
    echo -e "$(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Service Status Grid
    echo -e "${YELLOW}📊 MICROSERVICES STATUS:${NC}"
    printf "%-20s %-8s %-6s %s\n" "Service" "Status" "Port" "Description"
    echo "----------------------------------------"
    printf "%-20s %-8s %-6s %s\n" "API Gateway" "$(get_service_status api-gateway 8000)" "8000" "Main API Router"
    printf "%-20s %-8s %-6s %s\n" "Show Service" "$(get_service_status show-service 8001)" "8001" "Show Generation"
    printf "%-20s %-8s %-6s %s\n" "Content Service" "$(get_service_status content-service 8002)" "8002" "News Collection"
    printf "%-20s %-8s %-6s %s\n" "Audio Service" "$(get_service_status audio-service 8003)" "8003" "TTS & Audio"
    printf "%-20s %-8s %-6s %s\n" "Media Service" "$(get_service_status media-service 8004)" "8004" "Media Processing"
    printf "%-20s %-8s %-6s %s\n" "Speaker Service" "$(get_service_status speaker-service 8005)" "8005" "Voice Management"
    printf "%-20s %-8s %-6s %s\n" "Data Service" "$(get_service_status data-service 8006)" "8006" "Database Ops"
    printf "%-20s %-8s %-6s %s\n" "Analytics Service" "$(get_service_status analytics-service 8007)" "8007" "Analytics"
    echo ""
    
    # API Stats
    echo -e "${YELLOW}📈 PRODUCTION STATS:${NC}"
    printf "%-20s %s\n" "Total Shows:" "$(get_api_stats)"
    printf "%-20s %s\n" "Website:" "https://www.radiox.cloud"
    printf "%-20s %s\n" "API:" "https://api.radiox.cloud"
    echo ""
    
    # Latest Show
    echo -e "${YELLOW}🎙️ LATEST SHOW:${NC}"
    echo "$(get_latest_show)"
    echo ""
    
    # Live Logs Preview (last 3 lines from most active services)
    echo -e "${YELLOW}📋 LIVE ACTIVITY:${NC}"
    echo -e "${PURPLE}Show Service:${NC}"
    docker logs radiox-show-service --tail 1 2>/dev/null | sed 's/^/  /' || echo "  No logs available"
    
    echo -e "${PURPLE}Audio Service:${NC}"
    docker logs radiox-audio-service --tail 1 2>/dev/null | sed 's/^/  /' || echo "  No logs available"
    
    echo -e "${PURPLE}API Gateway:${NC}"
    docker logs radiox-api-gateway --tail 1 2>/dev/null | sed 's/^/  /' || echo "  No logs available"
    
    echo ""
    echo -e "${BLUE}💡 Commands: ${NC}[r] Restart Services | [l] Live Logs | [s] Service Status | [q] Quit"
    
    # Wait for input or timeout
    read -t 5 -n 1 input
    case $input in
        r|R)
            echo -e "\n${YELLOW}Restarting all services...${NC}"
            docker-compose restart
            sleep 3
            ;;
        l|L)
            echo -e "\n${YELLOW}Opening live logs...${NC}"
            docker-compose logs -f --tail=50
            ;;
        s|S)
            echo -e "\n${YELLOW}Service details...${NC}"
            docker-compose ps
            read -p "Press Enter to continue..."
            ;;
        q|Q)
            echo -e "\n${GREEN}Monitoring stopped. Auf Wiedersehen! 👋${NC}"
            exit 0
            ;;
    esac
done 