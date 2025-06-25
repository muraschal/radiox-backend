# 🔌 RadioX Port Architecture Documentation

<div align="center">

![Port Architecture](https://img.shields.io/badge/ports-architecture-blue)
![Docker](https://img.shields.io/badge/docker-compose-green)
![Network](https://img.shields.io/badge/network-radiox-orange)

**🏗️ Complete port mapping and network architecture for RadioX microservices**

</div>

---

## 🚨 CRITICAL: Port Consistency Rules

### **⚠️ NEVER AGAIN: Common Port Configuration Mistakes**

**❌ WHAT WENT WRONG BEFORE:**
- Data Service Dockerfile exposed port 8006 internally
- Docker Compose mapped `8006:8000` (external:internal)
- API Gateway expected `data-service:8000`
- Result: Connection refused in Docker network

**✅ SOLUTION IMPLEMENTED:**
- **ALL services run on port 8000 internally**
- **Docker Compose maps external ports to internal 8000**
- **API Gateway always connects to `service-name:8000`**

---

## 🎯 Port Architecture Overview

### **🏗️ Design Principles**

1. **Internal Consistency**: All microservices run on port 8000 internally
2. **External Differentiation**: Each service gets unique external port
3. **Gateway Routing**: API Gateway routes to `service:8000` internally
4. **Port Range**: 8000-8007 for services, 6379 for Redis
5. **No Port Conflicts**: Clear separation between internal/external

### **🔍 Why This Architecture?**

**Internal Port 8000 for All Services:**
- **Consistency**: Same port across all microservices
- **Simplicity**: API Gateway always connects to `:8000`
- **Docker Networking**: Services communicate via service names
- **Health Checks**: Uniform health check endpoints
- **Development**: Easy to remember and debug

**External Port Differentiation:**
- **Direct Access**: Each service accessible for debugging
- **Load Balancing**: Future proxy configurations
- **Monitoring**: Service-specific monitoring endpoints
- **Development**: Direct service testing capabilities

---

## 📊 Complete Port Mapping Table

| Service | Container Name | Internal Port | External Port | Docker Mapping | API Gateway Route |
|---------|---------------|---------------|---------------|----------------|-------------------|
| **API Gateway** | `radiox-api-gateway` | 8000 | 8000 | `8000:8000` | N/A (Entry Point) |
| **Show Service** | `radiox-show-service` | 8000 | 8001 | `8001:8000` | `show-service:8000` |
| **Content Service** | `radiox-content-service` | 8000 | 8002 | `8002:8000` | `content-service:8000` |
| **Audio Service** | `radiox-audio-service` | 8000 | 8003 | `8003:8000` | `audio-service:8000` |
| **Media Service** | `radiox-media-service` | 8000 | 8004 | `8004:8000` | `media-service:8000` |
| **Speaker Service** | `radiox-speaker-service` | 8000 | 8005 | `8005:8000` | `speaker-service:8000` |
| **Data Service** | `radiox-data-service` | 8000 | 8006 | `8006:8000` | `data-service:8000` |
| **Analytics Service** | `radiox-analytics-service` | 8000 | 8007 | `8007:8000` | `analytics-service:8000` |
| **Redis** | `radiox-redis` | 6379 | 6379 | `6379:6379` | `redis:6379` |

---

## 🔧 Configuration Files Consistency

### **📋 Required Consistency Across Files:**

#### **1. Dockerfile (ALL Services)**
```dockerfile
# ✅ CORRECT - Always port 8000 internally
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **2. docker-compose.yml**
```yaml
# ✅ CORRECT - External port varies, internal always 8000
data-service:
  ports:
    - "8006:8000"  # External:Internal
```

#### **3. API Gateway Service Configuration**
```python
# ✅ CORRECT - Always connect to port 8000 internally
SERVICES = {
    "data": {"url": "http://data-service:8000", "timeout": 30},
    "show": {"url": "http://show-service:8000", "timeout": 300},
    # ... all services use :8000
}
```

---

## 🌐 Network Architecture

### **🔗 Docker Network: `radiox-network`**

```
┌─────────────────────────────────────────────────────────────┐
│                    radiox-network (Bridge)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ api-gateway  │    │ show-service │    │content-service│  │
│  │   :8000      │◄──►│    :8000     │    │    :8000     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ data-service │    │audio-service │    │ redis        │  │
│  │   :8000      │    │    :8000     │    │  :6379       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **🔍 Communication Patterns:**

1. **External → API Gateway**: `https://api.radiox.cloud` → `container:8000`
2. **API Gateway → Services**: `service-name:8000` (internal Docker network)
3. **Services → Redis**: `redis:6379` (internal Docker network)
4. **Services → Supabase**: Direct HTTPS connection (external)

---

## 🧪 Port Testing & Validation

### **✅ Validation Checklist:**

#### **1. Internal Service Communication**
```bash
# Test from API Gateway container
docker exec radiox-api-gateway curl http://data-service:8000/health
docker exec radiox-api-gateway curl http://show-service:8000/health
```

#### **2. External Port Access**
```bash
# Test external access to each service
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Show Service (direct)
curl http://localhost:8006/health  # Data Service (direct)
```

#### **3. Production API Access**
```bash
# Test production endpoint
curl https://api.radiox.cloud/health
curl https://api.radiox.cloud/services/status
```

---

## 🚨 Port Conflict Prevention

### **🔒 Mandatory Pre-Deployment Checks:**

#### **1. Dockerfile Validation**
```bash
# Check all Dockerfiles use port 8000
find services/ -name "Dockerfile" -exec grep -H "EXPOSE\|--port" {} \;
# Expected: All should show port 8000
```

#### **2. Docker Compose Validation**
```bash
# Check port mappings
docker-compose config | grep -A 1 -B 1 "ports:"
# Expected: All internal ports should be 8000
```

#### **3. API Gateway Service URLs**
```bash
# Check service configurations
grep -r "service.*:8000" services/api-gateway/
# Expected: All service URLs end with :8000
```

---

## 📋 Troubleshooting Port Issues

### **🔍 Common Problems & Solutions:**

#### **Problem: "Connection Refused" in Docker Network**
```bash
# Diagnosis
docker exec radiox-api-gateway curl -v http://data-service:8000/health

# Common Causes:
# 1. Service runs on wrong internal port (not 8000)
# 2. Dockerfile EXPOSE doesn't match CMD port
# 3. Health check uses wrong port
```

#### **Problem: External Access Fails**
```bash
# Diagnosis
curl -v http://localhost:8006/health

# Common Causes:
# 1. Docker compose port mapping wrong
# 2. Service not running
# 3. Firewall blocking port
```

#### **Problem: API Gateway Can't Reach Service**
```bash
# Diagnosis
docker logs radiox-api-gateway | grep -i error
curl https://api.radiox.cloud/services/status

# Common Causes:
# 1. Service URL in gateway config wrong
# 2. Service container not in same network
# 3. Service startup failed
```

---

## 🎯 Port Assignment Strategy

### **📊 Why These Specific Ports?**

**Port 8000 (API Gateway):**
- **Standard**: Common HTTP alternative port
- **Production**: Maps directly to Cloudflare tunnel
- **Memorable**: Easy to remember as main entry point

**Ports 8001-8007 (Microservices):**
- **Sequential**: Easy to remember and manage
- **Non-conflicting**: Avoid common service ports
- **Debugging**: Direct access for development
- **Monitoring**: Service-specific health checks

**Port 6379 (Redis):**
- **Standard**: Redis default port
- **Consistency**: Same port internally and externally
- **Tools**: Redis clients expect this port

### **🔒 Reserved Port Ranges:**
- **8000-8007**: RadioX microservices
- **6379**: Redis
- **5432**: PostgreSQL (if added)
- **3000**: Frontend development server
- **9000-9999**: Future monitoring/admin tools

---

## 📚 Implementation Guidelines

### **🚀 Adding New Services:**

1. **Choose Next Available Port**: Use 8008, 8009, etc.
2. **Update Documentation**: Add to port mapping table
3. **Follow Consistency Rules**: Internal port always 8000
4. **Update API Gateway**: Add service configuration
5. **Test All Communication Paths**: Internal and external

### **🔧 Modifying Existing Services:**

1. **Never Change Internal Port**: Always keep 8000
2. **External Port Changes**: Update docker-compose.yml only
3. **Test After Changes**: Run port validation checklist
4. **Update Documentation**: Keep this document current

---

## 🎉 Success Criteria

### **✅ Port Architecture is Correct When:**

1. **All services respond** on internal port 8000
2. **API Gateway can reach** all services via `service:8000`
3. **External ports are unique** and accessible
4. **Production API works** via Cloudflare tunnel
5. **No connection refused errors** in service logs
6. **Health checks pass** for all services

---

## 📞 Emergency Port Recovery

### **🚨 If Port Configuration Breaks:**

1. **Stop all containers**: `docker-compose down`
2. **Validate configurations**: Run validation checklist
3. **Fix inconsistencies**: Update Dockerfiles/compose
4. **Rebuild affected services**: `docker-compose up -d --build`
5. **Test communication**: Run port testing checklist
6. **Verify production**: Test external API access

---

**📝 Document Version**: 1.0  
**Last Updated**: 2025-06-25  
**Next Review**: When adding new services  
**Owner**: RadioX Engineering Team 